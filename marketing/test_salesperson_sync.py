from importlib import import_module

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from Auth.models import Profile
from .models import Salesperson


class SalespersonSyncTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='alex', email='alex@example.com',
                                                        first_name='Alex', last_name='Smith')
        self.profile = Profile.objects.create(user=self.user, employee_id='SALES-1', department='Sales')

    def approve(self):
        self.profile.is_approved = True
        self.profile.save(update_fields=['is_approved'])
        return Salesperson.objects.get(user=self.user)

    def test_api_approval_creates_link_and_lists_person(self):
        self.assertFalse(Salesperson.objects.exists())
        admin = get_user_model().objects.create_user(username='admin', is_staff=True)
        client = APIClient()
        client.force_authenticate(admin)
        response = client.post(reverse('approve-user', args=[self.user.pk]), {'action': 'approve'})
        self.assertEqual(response.status_code, 200)
        person = Salesperson.objects.get(user=self.user)
        self.assertEqual((person.name, person.email, person.department), ('Alex Smith', self.user.email, 'Sales'))
        self.assertEqual(client.get(reverse('salesperson-list-create')).data[0]['id'], person.pk)
        client.post(reverse('approve-user', args=[self.user.pk]), {'action': 'approve'})
        self.assertEqual(Salesperson.objects.count(), 1)

    def test_other_departments_and_missing_profiles_do_not_create_people(self):
        self.profile.department = 'HR'
        self.profile.is_approved = True
        self.profile.save()
        get_user_model().objects.create_user(username='no-profile')
        self.assertFalse(Salesperson.objects.exists())
        self.profile.department = ' sales '
        self.profile.save()
        self.assertEqual(Salesperson.objects.get().user_id, self.user.pk)

    def test_user_updates_sync_and_ineligibility_deactivates_same_record(self):
        person = self.approve()
        self.user.first_name = 'Updated'
        self.user.email = 'updated@example.com'
        self.user.save()
        person.refresh_from_db()
        self.assertEqual((person.name, person.email), ('Updated Smith', 'updated@example.com'))
        for field, bad, good in [('is_approved', False, True), ('department', 'HR', 'Sales')]:
            setattr(self.profile, field, bad)
            self.profile.save()
            person.refresh_from_db()
            self.assertFalse(person.is_active)
            setattr(self.profile, field, good)
            self.profile.save()
            person.refresh_from_db()
            self.assertTrue(person.is_active)
        self.user.is_active = False
        self.user.save()
        person.refresh_from_db()
        self.assertFalse(person.is_active)
        self.user.is_active = True
        self.user.save()
        self.assertEqual(Salesperson.objects.get(user=self.user).pk, person.pk)

    def test_duplicate_names_do_not_claim_manual_records(self):
        manual = Salesperson.objects.create(name='Alex Smith', email=self.user.email)
        person = self.approve()
        self.assertNotEqual(person.pk, manual.pk)
        self.assertTrue(person.name.startswith('Alex Smith ('))
        manual.refresh_from_db()
        self.assertIsNone(manual.user_id)
        self.profile.save()
        self.assertEqual(Salesperson.objects.count(), 2)

    def test_blank_names_fall_back_to_email_then_username(self):
        self.user.first_name = self.user.last_name = ''
        self.user.save()
        person = self.approve()
        self.assertEqual(person.name, self.user.email)
        self.user.email = ''
        self.user.save()
        person.refresh_from_db()
        self.assertEqual(person.name, self.user.username)

    def test_profile_and_user_deletion_deactivate_but_preserve_person(self):
        person = self.approve()
        self.profile.delete()
        person.refresh_from_db()
        self.assertFalse(person.is_active)
        self.profile = Profile.objects.create(user=self.user, employee_id='SALES-1',
                                              department='Sales', is_approved=True)
        self.user.delete()
        person.refresh_from_db()
        self.assertIsNone(person.user_id)
        self.assertFalse(person.is_active)

    def test_backfill_is_idempotent_and_skips_ineligible_users(self):
        # QuerySet updates bypass signals, as existing rows before deployment did.
        Profile.objects.filter(pk=self.profile.pk).update(is_approved=True)
        hr = get_user_model().objects.create_user(username='hr')
        Profile.objects.create(user=hr, employee_id='HR-1', department='HR', is_approved=True)
        backfill = import_module('marketing.migrations.0006_link_approved_sales_users').link_approved_sales_users
        editor = connection.schema_editor()
        backfill(apps, editor)
        backfill(apps, editor)
        self.assertEqual(Salesperson.objects.get().user_id, self.user.pk)
