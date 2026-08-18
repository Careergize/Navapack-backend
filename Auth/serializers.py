from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import Profile
User = get_user_model()

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        # 1. Look up user by email address
        try:
            user_obj = User.objects.get(email__iexact=email)
            username = user_obj.get_username()
        except User.DoesNotExist:
            raise serializers.ValidationError('Unable to log in with provided credentials.')

        # 2. Authenticate using the username found
        user = authenticate(
            request=self.context.get('request'),
            username=username,
            password=password
        )

        if not user:
            raise serializers.ValidationError('Unable to log in with provided credentials.')

        attrs['user'] = user
        return attrs



class SignupSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    employee_id = serializers.CharField(max_length=50)
    department = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return value

    def validate_employee_id(self, value):
        if Profile.objects.filter(employee_id__iexact=value).exists():
            raise serializers.ValidationError('This Employee ID is already registered.')
        return value

    def create(self, validated_data):
        name_parts = validated_data['name'].strip().split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        user = User.objects.create_user(
            username=validated_data['email'],  # default User requires a username
            email=validated_data['email'],
            first_name=first_name,
            last_name=last_name,
            password=validated_data['password'],
        )

        Profile.objects.create(
            user=user,
            employee_id=validated_data['employee_id'],
            department=validated_data['department'],
        )

        return user


class UserListSerializer(serializers.ModelSerializer):
    employee_id = serializers.CharField(source='profile.employee_id')
    department = serializers.CharField(source='profile.department')
    is_approved = serializers.BooleanField(source='profile.is_approved')

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'employee_id', 'department', 'is_approved', 'date_joined')