from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from .models import CustomerPipeline, DailyActivity, Salesperson


class ContactEmailTests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(get_user_model().objects.create_user(username='admin', is_staff=True))
        self.person = Salesperson.objects.create(name='Rep')

    def cases(self):
        return ((CustomerPipeline, 'pipeline-list-create', 'pipeline-detail'),
                (DailyActivity, 'daily-activity-list-create', 'daily-activity-detail'))

    def payload(self, model):
        data = {'customer_company': 'Customer', 'salesperson': self.person.pk}
        if model is CustomerPipeline:
            data['prospect_id'] = f'PR-{model.objects.count()}'
            data['date_added'] = str(timezone.localdate())
        else:
            data['date'] = str(timezone.localdate())
        return data

    def test_email_round_trip_update_and_clear(self):
        for model, listing, detail in self.cases():
            with self.subTest(model=model):
                data = self.payload(model)
                data['email'] = 'contact@example.com'
                response = self.client.post(reverse(listing), data, format='json')
                self.assertEqual(response.status_code, 201, response.data)
                obj = model.objects.get(pk=response.data['id'])
                self.assertEqual(obj.email, data['email'])
                url = reverse(detail, args=[obj.pk])
                self.assertEqual(self.client.get(url).data['email'], data['email'])
                self.assertEqual(self.client.get(reverse(listing)).data[0]['email'], data['email'])
                for email in ('updated@example.com', ''):
                    response = self.client.patch(url, {'email': email}, format='json')
                    self.assertEqual(response.status_code, 200, response.data)
                    obj.refresh_from_db()
                    self.assertEqual(obj.email, email)

    def test_omitted_email_defaults_to_blank_and_invalid_email_is_rejected(self):
        for model, listing, detail in self.cases():
            with self.subTest(model=model):
                data = self.payload(model)
                response = self.client.post(reverse(listing), data, format='json')
                self.assertEqual(response.status_code, 201, response.data)
                self.assertEqual(response.data['email'], '')
                obj = model.objects.get(pk=response.data['id'])
                response = self.client.patch(reverse(detail, args=[obj.pk]),
                                             {'email': 'invalid-email'}, format='json')
                self.assertEqual(response.status_code, 400)
                self.assertIn('email', response.data)
                obj.refresh_from_db()
                self.assertEqual(obj.email, '')
                data = self.payload(model)
                data['email'] = 'invalid-email'
                response = self.client.post(reverse(listing), data, format='json')
                self.assertEqual(response.status_code, 400)
                self.assertIn('email', response.data)
