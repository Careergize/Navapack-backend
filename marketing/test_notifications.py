from datetime import date, timedelta
from unittest.mock import patch
from urllib.error import HTTPError
from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from Auth.models import Profile
from .models import CustomerPipeline, DailyActivity, FollowupNotification, Salesperson
from .notifications import process_followups, responsible_user, send_whatsapp


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
                   DEFAULT_FROM_EMAIL='crm@example.test')
class FollowupTests(TestCase):
    def setUp(self):
        self.today = date(2026, 10, 10)
        self.user = get_user_model().objects.create_user(username='alex', email='alex@example.test')
        self.person = Salesperson.objects.create(name='Alex', user=self.user,
            department='Marketing', phone='+256700000000')
        self.pipeline = CustomerPipeline.objects.create(prospect_id='PR-TEST',
            salesperson=self.person, customer_company='ABC', next_action='Call about quotation',
            next_followup_date=self.today)

    def run_notifications(self, today=None):
        with patch('marketing.notifications.send_whatsapp', return_value='wamid.test'):
            return process_followups(today or self.today)

    def test_dates_duplicate_prevention_and_manager_escalation(self):
        manager = get_user_model().objects.create_user(username='manager', email='manager@example.test')
        manager.groups.add(Group.objects.create(name='Management'))
        Profile.objects.create(user=manager, employee_id='M1', department='Marketing', is_approved=True)
        other = get_user_model().objects.create_user(username='other', email='other@example.test')
        other.groups.add(Group.objects.get(name='Management'))
        Profile.objects.create(user=other, employee_id='M2', department='Sales')
        for day, kind, count in [(self.today-timedelta(days=2), 'upcoming', 1),
                                 (self.today, 'due', 1), (self.today+timedelta(days=1), 'missed', 2)]:
            stats = self.run_notifications(day)
            self.assertEqual(stats[kind], 1)
            self.assertEqual(stats['email_sent'], count)
            self.assertEqual(stats['whatsapp_sent'], 1)
            self.assertEqual(self.run_notifications(day)['email_sent'], 0)
        self.assertEqual(mail.outbox[-1].to, ['manager@example.test'])
        self.assertEqual(self.run_notifications(self.today+timedelta(days=3))['email_sent'], 0)
        self.assertEqual(FollowupNotification.objects.count(), 7)

    def test_completed_and_closed_pipeline_suppressed(self):
        for field, value in [('followup_status', 'completed'), ('sales_stage', 'Won'), ('sales_stage', 'Lost')]:
            self.pipeline.followup_status = 'PENDING'
            self.pipeline.sales_stage = 'New Lead'
            setattr(self.pipeline, field, value)
            self.pipeline.save()
            self.assertFalse(self.run_notifications())
        self.assertFalse(FollowupNotification.objects.exists())

    def test_activity_alone_does_not_prove_completion(self):
        DailyActivity.objects.create(date=self.today, salesperson=self.person,
            customer_pipeline=self.pipeline, customer_company='ABC', discussion_outcome='Unrelated discussion')
        self.assertEqual(self.run_notifications()['email_sent'], 1)

    def test_email_failure_does_not_stop_whatsapp_or_next_customer(self):
        CustomerPipeline.objects.create(prospect_id='PR-OTHER', salesperson=self.person,
            customer_company='Other', next_followup_date=self.today)
        with patch('marketing.notifications.send_email', side_effect=[TimeoutError(), '']):
            stats = self.run_notifications()
        self.assertEqual(stats['email_sent'], 1)
        self.assertEqual(stats['whatsapp_sent'], 2)
        self.assertEqual(FollowupNotification.objects.filter(status='unknown').count(), 1)

    def test_whatsapp_failure_isolated_and_uncertain_send_not_retried(self):
        with patch('marketing.notifications.send_whatsapp', side_effect=TimeoutError()) as sender:
            self.assertEqual(process_followups(self.today)['email_sent'], 1)
            process_followups(self.today)
            self.assertEqual(sender.call_count, 1)

    def test_missing_contact_recorded_and_failed_channel_recovers(self):
        self.user.email = ''
        self.user.save()
        self.person.phone = ''
        self.person.save()
        stats = process_followups(self.today)
        self.assertEqual(stats['failed'], 2)
        self.user.email = 'fixed@example.test'
        self.user.save()
        self.assertEqual(self.run_notifications()['email_sent'], 1)

    def test_legacy_name_and_department_match_must_be_unique(self):
        self.person.user = None
        self.person.save()
        self.user.first_name = 'Alex'
        self.user.save()
        profile = Profile.objects.create(user=self.user, employee_id='A1', department='Sales', is_approved=True)
        self.assertIsNone(responsible_user(self.person))
        profile.department = 'Marketing'
        profile.save()
        self.assertEqual(responsible_user(self.person), self.user)
        duplicate = get_user_model().objects.create_user(username='duplicate', first_name='Alex')
        Profile.objects.create(user=duplicate, employee_id='A2', department='Marketing', is_approved=True)
        self.assertIsNone(responsible_user(self.person))

    def test_missing_manager_audited(self):
        self.run_notifications(self.today+timedelta(days=1))
        self.assertTrue(FollowupNotification.objects.filter(notification_type='escalation', status='failed').exists())

    def test_marketing_sales_only_and_inactive_users(self):
        for department, active in [('Finance', True), ('Sales', False)]:
            self.person.department = department
            self.person.save()
            self.user.is_active = active
            self.user.save()
            self.assertEqual(self.run_notifications()['failed'], 2)
        self.assertEqual(len(mail.outbox), 0)

    def test_sending_claim_never_resent(self):
        FollowupNotification.objects.create(customer_pipeline=self.pipeline,
            notification_type='due', scheduled_for=self.today, recipient_key=f'salesperson:{self.person.pk}',
            channel='email', status='sending')
        self.assertEqual(self.run_notifications()['email_sent'], 0)

    def test_history_management_only(self):
        client = APIClient()
        url = reverse('followup-notifications')
        self.assertIn(client.get(url).status_code, (401, 403))
        client.force_authenticate(self.user)
        self.assertEqual(client.get(url).status_code, 403)
        self.user.groups.add(Group.objects.create(name='Management'))
        self.run_notifications()
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertNotIn('WHATSAPP_ACCESS_TOKEN', str(response.data))

    def test_command_dry_run(self):
        output = StringIO()
        call_command('send_followup_notifications', date=self.today, dry_run=True, stdout=output)
        self.assertIn('Due today: 1', output.getvalue())
        self.assertFalse(FollowupNotification.objects.exists())

    def test_new_followup_date_starts_new_cycle(self):
        self.run_notifications()
        self.pipeline.next_followup_date = self.today + timedelta(days=5)
        self.pipeline.save()
        stats = self.run_notifications(self.pipeline.next_followup_date)
        self.assertEqual(stats['email_sent'], 1)
        self.assertEqual(FollowupNotification.objects.count(), 4)

    def test_local_timezone_determines_due_date(self):
        from datetime import datetime, timezone as dt_timezone
        from django.utils import timezone
        with timezone.override('Asia/Kolkata'), patch('django.utils.timezone.now',
            return_value=datetime(2026, 10, 9, 20, tzinfo=dt_timezone.utc)), \
            patch('marketing.notifications.send_whatsapp', return_value='wamid.test'):
            self.assertEqual(process_followups()['due'], 1)

    def test_database_rejects_duplicate_delivery(self):
        from django.db import IntegrityError, transaction
        self.run_notifications()
        with self.assertRaises(IntegrityError), transaction.atomic():
            FollowupNotification.objects.create(customer_pipeline=self.pipeline,
                notification_type='due', scheduled_for=self.today,
                recipient_key=f'salesperson:{self.person.pk}', channel='email')

    @override_settings(WHATSAPP_PROVIDER='meta', WHATSAPP_API_URL='https://graph.facebook.com/vTEST/{phone_number_id}/messages',
        WHATSAPP_PHONE_NUMBER_ID='123', WHATSAPP_ACCESS_TOKEN='test-token', WHATSAPP_TEMPLATES={'due': 'due_template'})
    def test_meta_template_payload(self):
        row = FollowupNotification(notification_type='due', recipient_name='Alex', destination=self.person.phone)
        with patch('marketing.notifications.urlopen') as request:
            request.return_value.__enter__.return_value.read.return_value = b'{"messages":[{"id":"wamid.test"}]}'
            self.assertEqual(send_whatsapp(row, self.pipeline), 'wamid.test')
            import json
            payload = json.loads(request.call_args.args[0].data)
            self.assertEqual(payload['template']['name'], 'due_template')
            self.assertEqual(payload['to'], '256700000000')
            self.assertEqual(len(payload['template']['components'][0]['parameters']), 4)

    def test_definitive_whatsapp_rejection_retries_only_failed_channel(self):
        with patch('marketing.notifications.send_whatsapp', side_effect=HTTPError('https://example.test', 400, 'Bad request', {}, None)):
            stats = process_followups(self.today)
        self.assertEqual(stats['email_sent'], 1)
        self.assertEqual(self.run_notifications()['email_sent'], 0)
        self.assertEqual(FollowupNotification.objects.get(channel='whatsapp').attempts, 2)
