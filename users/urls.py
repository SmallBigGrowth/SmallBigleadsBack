from django.urls import path
from .views import RegisterView, LogoutAPIView, SetNewPasswordAPIView,VerifyEmail, LoginAPIView,PasswordTokenCheckAPI, RequestPasswordResetEmail, RequestEmailUpdate, ConfirmEmailUpdate ,UpdateProfileView, SubscriptionStatusView,ReferralStatsView, Enable2FAView, VerifyOTPView, ActivityLogView

urlpatterns = [
    path('register/', RegisterView.as_view(), name="register"),
    path('login/', LoginAPIView.as_view(), name="login"),
    path('logout/', LogoutAPIView.as_view(), name="logout"),
    path('email-verify/', VerifyEmail.as_view(), name="email-verify"),
    path('request-reset-email/', RequestPasswordResetEmail.as_view(), name="request-reset-email"),
    path('password-reset/<uidb64>/<token>/', PasswordTokenCheckAPI.as_view(), name='password-reset-confirm'),
    path('password-reset-complete/', SetNewPasswordAPIView.as_view(), name='password-reset-complete'),
    path('profile/update/', UpdateProfileView.as_view(), name='profile-update'),
    path('subscription/status/', SubscriptionStatusView.as_view(), name='subscription-status'),
    path('referrals/stats/', ReferralStatsView.as_view(), name='referral-stats'),
    path('2fa/enable/', Enable2FAView.as_view(), name='2fa-enable'),
    path('2fa/verify/', VerifyOTPView.as_view(), name='2fa-verify'),
    path('activity/log/', ActivityLogView.as_view(), name='activity-log'),
    path('request-email-update/', RequestEmailUpdate.as_view(), name="request-email-update"),
    path('confirm-email-update/', ConfirmEmailUpdate.as_view(), name="confirm-email-update"),
]