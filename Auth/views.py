from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from .serializers import LoginSerializer
from .serializers import SignupSerializer
from .serializers import UserListSerializer


class LoginAPIView(APIView):
    """
    API View to authenticate users via Email and Password.
    Returns auth token and basic user info upon success.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        # Use getattr instead of user.profile directly — if this user has no
        # related Profile row (e.g. created via admin/createsuperuser/seed
        # script, or before a profile-creation signal existed), user.profile
        # raises RelatedObjectDoesNotExist and Django turns that into a 500.
        profile = getattr(user, 'profile', None)

        return Response({
            'token': token.key,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'department': profile.department if profile else None,
            }
        }, status=status.HTTP_200_OK)


class SignupAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        profile = getattr(user, 'profile', None)

        return Response({
            'message': 'Account created successfully. Please wait for administrator approval before logging in.',
            'user': {
                'id': user.id,
                'email': user.email,
                'name': f"{user.first_name} {user.last_name}".strip(),
                'employee_id': profile.employee_id if profile else None,
                'department': profile.department if profile else None,
                'is_approved': profile.is_approved if profile else False,
            }
        }, status=status.HTTP_201_CREATED)


class UserListAPIView(APIView):
    """List all users with profile details."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        users = User.objects.select_related('profile').all().order_by('-date_joined')
        serializer = UserListSerializer(users, many=True)
        return Response(serializer.data)


class PendingUsersAPIView(APIView):
    """List all users awaiting approval, for the admin dashboard."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        pending = User.objects.filter(profile__is_approved=False).order_by('-date_joined')
        serializer = UserListSerializer(pending, many=True)
        return Response(serializer.data)


class ApproveUserAPIView(APIView):
    """Approve or reject a pending user."""
    permission_classes = [IsAdminUser]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action')  # 'approve' or 'reject'

        if action == 'approve':
            user.profile.is_approved = True
            user.profile.save(update_fields=['is_approved'])
            return Response({'detail': f'{user.email} has been approved.'})
        elif action == 'reject':
            user.delete()  # cascades and deletes the Profile too
            return Response({'detail': 'User has been rejected and removed.'})
        else:
            return Response({'detail': 'Invalid action. Use "approve" or "reject".'}, status=400)