from django.test import SimpleTestCase
from django.urls import reverse


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
