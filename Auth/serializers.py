from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

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