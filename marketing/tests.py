from django.test import SimpleTestCase
from django.urls import reverse
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from rest_framework.test import APITestCase
from .models import Salesperson, CustomerPipeline, DailyActivity


class SalesRecordSecurityTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='sales')
        self.owner = Salesperson.objects.create(name='Sales', user=self.user)
        self.other = Salesperson.objects.create(name='Other')
        self.admin = User.objects.create_user(username='admin', is_staff=True)
        self.manager = User.objects.create_user(username='manager')
        self.manager.groups.add(Group.objects.create(name='Management'))
        self.client.force_authenticate(self.user)
        self.today = timezone.localdate()

    def cases(self):
        return (
            (CustomerPipeline, 'date_added', 'pipeline-list-create', 'pipeline-detail'),
            (DailyActivity, 'date', 'daily-activity-list-create', 'daily-activity-detail'),
        )

    def record(self, model, field, owner=None, date=None):
        data = dict(salesperson=owner or self.owner, customer_company='Original')
        data[field] = date or self.today
        if model is CustomerPipeline:
            data['prospect_id'] = f'PR-{model.objects.count() + 1}'
        return model.objects.create(**data)

    def test_other_owner_and_non_today_records_return_403_before_validation(self):
        for model, field, _, detail in self.cases():
            for owner, date in ((self.other, self.today),
                                (self.owner, self.today - timedelta(days=1)),
                                (self.owner, self.today + timedelta(days=1))):
                obj = self.record(model, field, owner, date)
                for method in ('put', 'patch', 'delete'):
                    with self.subTest(model=model, method=method, date=date, owner=owner):
                        response = getattr(self.client, method)(reverse(detail, args=[obj.pk]),
                            {field: str(self.today), 'salesperson': self.owner.pk}, format='json')
                        self.assertEqual(response.status_code, 403)
                        obj.refresh_from_db()
                        self.assertEqual(getattr(obj, field), date)
                        self.assertEqual(obj.salesperson_id, owner.pk)

    def test_own_today_updates_ignore_owner_and_date_even_if_invalid(self):
        for model, field, _, detail in self.cases():
            obj = self.record(model, field)
            for method in ('put', 'patch'):
                response = getattr(self.client, method)(reverse(detail, args=[obj.pk]),
                    {'customer_company': 'Changed', 'salesperson': 'invalid', field: 'invalid'}, format='json')
                self.assertEqual(response.status_code, 200, response.data)
                obj.refresh_from_db()
                self.assertEqual(obj.customer_company, 'Changed')
                self.assertEqual(obj.salesperson_id, self.owner.pk)
                self.assertEqual(getattr(obj, field), self.today)

    def test_creation_forces_owner_and_date_and_accepts_omitted_fields(self):
        for model, field, listing, _ in self.cases():
            for supplied in (False, True):
                data = {'customer_company': 'Created'}
                if model is CustomerPipeline:
                    data['prospect_id'] = f'CREATE-{supplied}'
                if supplied:
                    data.update(salesperson='invalid', **{field: 'invalid'})
                response = self.client.post(reverse(listing), data, format='json')
                self.assertEqual(response.status_code, 201, response.data)
                obj = model.objects.get(pk=response.data['id'])
                self.assertEqual(obj.salesperson_id, self.owner.pk)
                self.assertEqual(getattr(obj, field), self.today)

    def test_management_can_change_historical_owner_and_date_and_create(self):
        for user in (self.admin, self.manager):
            self.client.force_authenticate(user)
            for model, field, listing, detail in self.cases():
                obj = self.record(model, field, self.other, self.today - timedelta(days=2))
                data = {'salesperson': self.owner.pk, field: str(self.today - timedelta(days=1))}
                response = self.client.patch(reverse(detail, args=[obj.pk]), data, format='json')
                self.assertEqual(response.status_code, 200, response.data)
                obj.refresh_from_db()
                self.assertEqual(obj.salesperson_id, self.owner.pk)
                self.assertEqual(getattr(obj, field), self.today - timedelta(days=1))
                data['customer_company'] = 'Management'
                if model is CustomerPipeline:
                    data['prospect_id'] = f'MANAGEMENT-{user.pk}'
                response = self.client.post(reverse(listing), data, format='json')
                self.assertEqual(response.status_code, 201, response.data)
                self.assertEqual(response.data[field], data[field])

    def test_unlinked_or_inactive_salesperson_cannot_write(self):
        user = get_user_model().objects.create_user(username='unlinked')
        for user in (user, self.user):
            self.owner.is_active = False
            self.owner.save()
            self.client.force_authenticate(user)
            for _, _, listing, _ in self.cases():
                self.assertEqual(self.client.post(reverse(listing), {}, format='json').status_code, 403)

    def test_timezone_local_day_controls_creation(self):
        from unittest.mock import patch
        from datetime import datetime, timezone as dt_timezone
        with timezone.override('Asia/Kolkata'), patch('django.utils.timezone.now',
                return_value=datetime(2026, 10, 2, 20, tzinfo=dt_timezone.utc)):
            response = self.client.post(reverse('daily-activity-list-create'),
                {'customer_company': 'Local day'}, format='json')
            self.assertEqual(response.status_code, 201, response.data)
            self.assertEqual(response.data['date'], '2026-10-03')


class LookupUrlTests(SimpleTestCase):
    def test_lookup_routes_resolve(self):
        self.assertEqual(reverse('product-service-list-create'), '/api/product-services/')
        self.assertEqual(reverse('product-service-detail', args=[1]), '/api/product-services/1/')
        self.assertEqual(reverse('sales-stage-list-create'), '/api/sales-stages/')
        self.assertEqual(reverse('sales-stage-detail', args=[1]), '/api/sales-stages/1/')
        self.assertEqual(reverse('activity-type-list-create'), '/api/activity-types/')
        self.assertEqual(reverse('activity-type-detail', args=[1]), '/api/activity-types/1/')
        self.assertEqual(reverse('unit-list-create'), '/api/units/')
        self.assertEqual(reverse('unit-detail', args=[1]), '/api/units/1/')
