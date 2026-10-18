from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Salesperson


class MarketingPasswordPermission(BasePermission):
    def has_permission(self, request, view):
        profile = getattr(request.user, 'profile', None)
        return bool(profile and profile.is_approved
                    and 'marketing' in profile.department.strip().lower())


class PasswordInput(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return data


class SalespersonPasswordAPIView(APIView):
    permission_classes = [IsAuthenticated, MarketingPasswordPermission]

    def post(self, request, pk):
        person = get_object_or_404(Salesperson.objects.select_related('user__profile'), pk=pk)
        account = person.user
        if account is None:
            return Response({'error': 'This salesperson has no linked login account.'}, status=400)
        profile = getattr(account, 'profile', None)
        department = (profile.department if profile else '').strip().lower()
        # Password delegation is based on the login department, not admin flags.
        if department != 'sales':
            return Response({'error': f'The selected salesperson is linked to an account in the "{department or "Unassigned"}" department. Select a Sales login account. Your Marketing login is authorized; this restriction applies to the selected account.'}, status=403)
        serializer = PasswordInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            validate_password(serializer.validated_data['new_password'], user=account)
        except ValidationError as exc:
            return Response({'new_password': exc.messages}, status=400)
        with transaction.atomic():
            account.set_password(serializer.validated_data['new_password'])
            account.save(update_fields=['password'])
            Token.objects.filter(user=account).delete()
        return Response({'message': 'Password updated. The salesperson must log in again.'})
