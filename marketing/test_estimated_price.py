from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from .models import CustomerPipeline, Salesperson


class EstimatedPriceTests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(get_user_model().objects.create_user(username='admin', is_staff=True))
        self.person = Salesperson.objects.create(name='Rep')
        self.data = {'prospect_id': 'PRICE-1', 'customer_company': 'Customer',
                     'salesperson': self.person.pk, 'date_added': str(timezone.localdate())}
        self.url = reverse('pipeline-list-create')

    def test_create_read_and_update_price(self):
        response = self.client.post(self.url, {**self.data, 'estimated_price': '1250.75'}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        obj = CustomerPipeline.objects.get(pk=response.data['id'])
        self.assertEqual(obj.estimated_price, Decimal('1250.75'))
        detail = reverse('pipeline-detail', args=[obj.pk])
        self.assertEqual(self.client.get(detail).data['estimated_price'], '1250.75')
        self.assertEqual(self.client.get(self.url).data[0]['estimated_price'], '1250.75')
        response = self.client.patch(detail, {'estimated_price': '99.50'}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        obj.refresh_from_db()
        self.assertEqual(obj.estimated_price, Decimal('99.50'))
        self.assertEqual(obj.estimated_value_ugx, Decimal('0'))

    def test_default_and_invalid_prices(self):
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['estimated_price'], '0.00')
        detail = reverse('pipeline-detail', args=[response.data['id']])
        for price in ('invalid', '1.234', '10000000000000.00'):
            with self.subTest(price=price):
                response = self.client.patch(detail, {'estimated_price': price}, format='json')
                self.assertEqual(response.status_code, 400)
                self.assertIn('estimated_price', response.data)
