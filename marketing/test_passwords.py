from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from Auth.models import Profile
from .models import Salesperson


class SalespersonPasswordTests(TestCase):
    def setUp(self):
        self.marketer = get_user_model().objects.create_user(username='marketer')
        Profile.objects.create(user=self.marketer, employee_id='M1', department='Marketing', is_approved=True)
        self.rep = get_user_model().objects.create_user(username='rep', password='OriginalSecret!734')
        Profile.objects.create(user=self.rep, employee_id='S1', department='Sales', is_approved=True)
        self.person, _ = Salesperson.objects.update_or_create(user=self.rep, defaults={'name': 'Rep'})
        self.url = reverse('salesperson-password', args=[self.person.pk])
        self.client = APIClient()
        self.payload = {'new_password': 'UpdatedSecret!8392', 'confirm_password': 'UpdatedSecret!8392'}

    def test_marketing_updates_password_and_revokes_token(self):
        self.client.force_authenticate(self.marketer)
        Token.objects.create(user=self.rep)
        self.assertEqual(self.client.post(self.url, self.payload).status_code, 200)
        self.rep.refresh_from_db()
        self.assertTrue(self.rep.check_password(self.payload['new_password']))
        self.assertFalse(Token.objects.filter(user=self.rep).exists())

    def test_other_departments_sales_and_unapproved_users_denied(self):
        self.client.force_authenticate(self.rep)
        self.assertEqual(self.client.post(self.url, self.payload).status_code, 403)
        for fields in [{'is_approved': False}, {'is_approved': True, 'department': 'Production'}]:
            Profile.objects.filter(user=self.marketer).update(**fields)
            user = get_user_model().objects.get(pk=self.marketer.pk)
            self.client.force_authenticate(user)
            self.assertEqual(self.client.post(self.url, self.payload).status_code, 403)

    def test_invalid_passwords_do_not_change_account(self):
        self.client.force_authenticate(self.marketer)
        for payload in [{}, {**self.payload, 'confirm_password': 'different'},
                        {'new_password': '123', 'confirm_password': '123'}]:
            self.assertEqual(self.client.post(self.url, payload).status_code, 400)
        self.rep.refresh_from_db()
        self.assertTrue(self.rep.check_password('OriginalSecret!734'))

    def test_sales_admin_flags_do_not_block_and_unlinked_accounts_rejected(self):
        self.client.force_authenticate(self.marketer)
        unlinked = Salesperson.objects.create(name='No login')
        self.assertEqual(self.client.post(reverse('salesperson-password', args=[unlinked.pk]), self.payload).status_code, 400)
        self.rep.is_staff = True
        self.rep.is_superuser = True
        self.rep.save()
        self.rep.groups.add(Group.objects.create(name='Management'))
        self.assertEqual(self.client.post(self.url, self.payload).status_code, 200)
        self.rep.refresh_from_db()
        self.assertTrue(self.rep.check_password(self.payload['new_password']))

    def test_anonymous_denied(self):
        self.assertIn(self.client.post(self.url, self.payload).status_code, (401, 403))

    def test_target_login_department_controls_access(self):
        self.client.force_authenticate(self.marketer)
        for department in ['Marketing', 'Production', 'Sales and Marketing', '']:
            Profile.objects.filter(user=self.rep).update(department=department)
            self.assertEqual(self.client.post(self.url, self.payload).status_code, 403)
        Profile.objects.filter(user=self.rep).update(department=' Sales ')
        self.assertEqual(self.client.post(self.url, self.payload).status_code, 200)
