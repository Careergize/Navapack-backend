from django.urls import path
from .views import (
    LoginAPIView,
    SignupAPIView,
    UserListAPIView,
    PendingUsersAPIView,
    ApproveUserAPIView,
)

urlpatterns = [
    path('login/', LoginAPIView.as_view(), name='login'),
    path('signup/', SignupAPIView.as_view(), name='signup'),
    path('users/', UserListAPIView.as_view(), name='users'),
    path('admin/pending-users/', PendingUsersAPIView.as_view(), name='pending-users'),
    path('admin/approve-user/<int:user_id>/', ApproveUserAPIView.as_view(), name='approve-user'),
]