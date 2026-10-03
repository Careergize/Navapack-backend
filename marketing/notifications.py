"""Durable, per-channel follow-up delivery. No automatic retry of uncertain sends."""
import json
import logging
import re
from collections import Counter
from datetime import timedelta
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone

from .models import CustomerPipeline, FollowupNotification

logger = logging.getLogger(__name__)
TITLES = {'upcoming': 'Upcoming Customer Follow-up', 'due': 'Customer Follow-up Due Today',
          'missed': 'Missed Customer Follow-up', 'escalation': 'Missed Customer Follow-up Escalation'}
INSTRUCTIONS = {'upcoming': 'Please prepare for the upcoming follow-up.',
                'due': 'Please complete the follow-up today.',
                'missed': 'Please complete the pending follow-up.',
                'escalation': 'Please review this missed follow-up with the responsible employee.'}


def responsible_user(salesperson):
    """Prefer explicit ownership. Legacy fallback must match both name and department uniquely."""
    if salesperson.user_id:
        return salesperson.user if salesperson.user.is_active else None
    matches = [user for user in get_user_model().objects.filter(is_active=True,
        profile__is_approved=True, profile__department__iexact=salesperson.department.strip())
        if (user.get_full_name().strip().casefold() == salesperson.name.strip().casefold()
            or user.username.casefold() == salesperson.name.strip().casefold())]
    return matches[0] if len(matches) == 1 else None


def managers(department):
    # Management is the application's existing manager role. Staff is an admin permission,
    # not evidence that an employee manages this department.
    return get_user_model().objects.filter(is_active=True, groups__name='Management').filter(
        Q(profile__department__iexact=department) |
        Q(salesperson__department__iexact=department, salesperson__is_active=True)).distinct()


def send_email(delivery, pipeline):
    if not settings.DEFAULT_FROM_EMAIL or not delivery.destination:
        raise ValidationError('Missing sender or recipient email configuration.')
    validate_email(delivery.destination)
    context = {'pipeline': pipeline, 'recipient': delivery.recipient_name,
               'title': TITLES[delivery.notification_type],
               'instruction': INSTRUCTIONS[delivery.notification_type]}
    message = EmailMultiAlternatives(
        f'{context["title"]} – {pipeline.customer_company}',
        render_to_string('marketing/followup_email.txt', context),
        settings.DEFAULT_FROM_EMAIL, [delivery.destination])
    message.attach_alternative(render_to_string('marketing/followup_email.html', context), 'text/html')
    if message.send(fail_silently=False) != 1:
        raise ValidationError('Email backend did not accept the message.')
    return ''


def send_whatsapp(delivery, pipeline):
    if settings.WHATSAPP_PROVIDER != 'meta':
        raise ValidationError('Configure WHATSAPP_PROVIDER=meta or implement your provider adapter.')
    template = settings.WHATSAPP_TEMPLATES.get(delivery.notification_type)
    if not all((template, settings.WHATSAPP_ACCESS_TOKEN, settings.WHATSAPP_PHONE_NUMBER_ID,
                settings.WHATSAPP_API_URL)):
        raise ValidationError('Missing WhatsApp API or approved template configuration.')
    url = settings.WHATSAPP_API_URL.format(phone_number_id=settings.WHATSAPP_PHONE_NUMBER_ID)
    if urlparse(url).scheme != 'https' or urlparse(url).hostname != 'graph.facebook.com':
        raise ValidationError('Meta WhatsApp requires an HTTPS graph.facebook.com messages URL.')
    raw = delivery.destination.strip()
    if not re.fullmatch(r'\+?[1-9][0-9 ()-]{7,25}', raw):
        raise ValidationError('WhatsApp number must include country code.')
    phone = re.sub(r'[^0-9]', '', raw)
    if not 8 <= len(phone) <= 15:
        raise ValidationError('Invalid international WhatsApp number length.')
    values = [delivery.recipient_name, pipeline.customer_company,
              pipeline.next_followup_date.strftime('%d %B %Y'), pipeline.next_action or 'Not specified']
    payload = {'messaging_product': 'whatsapp', 'to': phone, 'type': 'template',
        'template': {'name': template, 'language': {'code': settings.WHATSAPP_TEMPLATE_LANGUAGE},
            'components': [{'type': 'body', 'parameters': [
                {'type': 'text', 'text': value} for value in values]}]}}
    request = Request(url, data=json.dumps(payload).encode(), method='POST', headers={
        'Authorization': f'Bearer {settings.WHATSAPP_ACCESS_TOKEN}', 'Content-Type': 'application/json'})
    with urlopen(request, timeout=settings.WHATSAPP_TIMEOUT) as response:
        return json.load(response)['messages'][0]['id']


def deliver(pipeline, kind, key, name, department, channel, destination, stats, routing_error=''):
    row, _ = FollowupNotification.objects.get_or_create(customer_pipeline=pipeline,
        notification_type=kind, scheduled_for=pipeline.next_followup_date,
        recipient_key=key, channel=channel,
        defaults={'recipient_name': name, 'department': department, 'destination': destination})
    # Commit the claim BEFORE contacting the provider. Concurrent command runs cannot resend.
    with transaction.atomic():
        row = FollowupNotification.objects.select_for_update().get(pk=row.pk)
        if row.status not in ('pending', 'failed'):
            stats['already_notified'] += 1
            return
        row.destination, row.recipient_name, row.department = destination, name, department
        row.status, row.error = 'sending', ''
        row.attempts += 1
        row.save()
    try:
        if routing_error:
            raise ValidationError(routing_error)
        provider_id = send_email(row, pipeline) if channel == 'email' else send_whatsapp(row, pipeline)
    except ValidationError as exc:
        row.status, row.error = 'failed', '; '.join(exc.messages)[:255]
        stats['failed'] += 1
    except HTTPError as exc:
        # 5xx can occur after acceptance; do not retry an uncertain delivery.
        row.status = 'failed' if 400 <= exc.code < 500 else 'unknown'
        row.error = f'WhatsApp HTTP {exc.code}; response body omitted.'
        stats['failed'] += 1
    except Exception as exc:
        row.status = 'unknown'
        row.error = f'{type(exc).__name__}: delivery outcome uncertain; review before retry.'
        stats['failed'] += 1
    else:
        row.status, row.provider_message_id = 'sent', provider_id
        stats[channel + '_sent'] += 1
    row.save()
    if row.status != 'sent':
        logger.warning('Follow-up delivery %s: %s (%s)', row.pk, row.status, row.error)


def process_followups(today=None, dry_run=False):
    today = today or timezone.localdate()
    stats = Counter()
    queryset = CustomerPipeline.objects.select_related('salesperson__user').filter(
        Q(next_followup_date=today + timedelta(days=2)) | Q(next_followup_date__lte=today)
    ).exclude(followup_status__iexact='COMPLETED').exclude(
        Q(sales_stage__iexact='Won') | Q(sales_stage__iexact='Lost'))
    for pipeline in queryset.iterator():
        kind = 'upcoming' if pipeline.next_followup_date > today else (
            'due' if pipeline.next_followup_date == today else 'missed')
        stats[kind] += 1
        if dry_run:
            continue
        try:
            person = pipeline.salesperson
            department = person.department.strip()
            user = responsible_user(person)
            error = ''
            if not person.is_active or department.casefold() not in ('sales', 'marketing'):
                error = 'Responsible employee is inactive or outside Sales/Marketing.'
            elif person.user_id and not user:
                error = 'Linked responsible user is inactive.'
            elif not person.user_id and not user:
                error = 'Link a user or supply one unique approved name-and-department match.'
            email = (user.email if user and user.email else person.email).strip()
            for channel, destination in [('email', email), ('whatsapp', person.phone.strip())]:
                deliver(pipeline, kind, f'salesperson:{person.pk}', person.name,
                    department, channel, destination, stats, error)
            if kind == 'missed':
                recipients = list(managers(department))
                if not recipients:
                    deliver(pipeline, 'escalation', 'manager:unresolved', '', department,
                        'email', '', stats, 'No active Management user for this department.')
                for manager in recipients:
                    deliver(pipeline, 'escalation', f'user:{manager.pk}',
                        manager.get_full_name() or manager.username, department, 'email',
                        manager.email.strip(), stats)
        except Exception as exc:
            stats['failed'] += 1
            # Never log external exception messages: they can contain credentials.
            logger.error('Pipeline %s processing failed: %s', pipeline.pk, type(exc).__name__)
    return stats
