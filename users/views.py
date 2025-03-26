from django.shortcuts import render
from rest_framework import generics, status, views, permissions
from .serializers import (
    RegisterSerializer, SetNewPasswordSerializer, ResetPasswordEmailRequestSerializer,
    EmailVerificationSerializer, LoginSerializer, LogoutSerializer, UserProfileSerializer,
    SubscriptionSerializer, OTPSerializer, UserActivitySerializer,
    EmailUpdateRequestSerializer, EmailUpdateConfirmSerializer
)
from django.utils.encoding import force_bytes, force_str
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, UserActivity
from .utils import Util
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
import jwt
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.http import HttpResponsePermanentRedirect
import os
import pyotp
import logging
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.core.mail import send_mail


logger = logging.getLogger(__name__)

class CustomRedirect(HttpResponsePermanentRedirect):
    allowed_schemes = [os.environ.get('APP_SCHEME', 'http'), 'http', 'https']

class RegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request):
        logger.info("Starting user registration process")
        user = request.data
        serializer = self.serializer_class(data=user)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            user_data = serializer.data
            user = User.objects.get(email=user_data['email'])
            token = RefreshToken.for_user(user).access_token
            current_site = get_current_site(request).domain
            relative_link = reverse('email-verify')
            absurl = 'http://' + current_site + relative_link + "?token=" + str(token)
            email_body = f'Hi {user.username}, Use the link below to verify your email:\n{absurl}'
            data = {'email_body': email_body, 'to_email': user.email, 'email_subject': 'Verify your email'}
            logger.debug(f"Sending verification email to {user.email}")
            Util.send_email(data)
            UserActivity.objects.create(user=user, action="User registered")
            logger.info(f"User {user.email} registered successfully")
            return Response(user_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Registration failed: {str(e)}")
            raise

class VerifyEmail(views.APIView):
    serializer_class = EmailVerificationSerializer
    token_param_config = openapi.Parameter('token', in_=openapi.IN_QUERY, description='Description', type=openapi.TYPE_STRING)

    @swagger_auto_schema(manual_parameters=[token_param_config])
    def get(self, request):
        token = request.GET.get('token')
        logger.info("Starting email verification process")
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user = User.objects.get(id=payload['user_id'])
            if not user.is_verified:
                user.is_verified = True
                user.save()
                UserActivity.objects.create(user=user, action="Email verified")
                logger.info(f"Email verified for user {user.email}")
            return Response({'email': 'Successfully activated'}, status=status.HTTP_200_OK)
        except jwt.ExpiredSignatureError:
            logger.error("Token expired during email verification")
            return Response({'error': 'Activation Expired'}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.exceptions.DecodeError:
            logger.error("Invalid token provided for email verification")
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Email verification failed: {str(e)}")
            raise

class LoginAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        logger.info("Starting user login process")
        serializer = self.serializer_class(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = User.objects.get(email=serializer.validated_data['email'])
            UserActivity.objects.create(user=user, action="User logged in")
            logger.info(f"User {user.email} logged in successfully")
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            raise

class RequestPasswordResetEmail(generics.GenericAPIView):
    serializer_class = ResetPasswordEmailRequestSerializer

    def post(self, request):
        logger.info("Starting password reset email request")
        serializer = self.serializer_class(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            email = request.data.get('email', '')
            if User.objects.filter(email=email).exists():
                user = User.objects.get(email=email)
                uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
                token = PasswordResetTokenGenerator().make_token(user)
                current_site = get_current_site(request).domain
                relative_link = reverse('password-reset-confirm', kwargs={'uidb64': uidb64, 'token': token})
                absurl = 'http://' + current_site + relative_link
                email_body = f'Hello,\nUse the link below to reset your password:\n{absurl}'
                data = {'email_body': email_body, 'to_email': user.email, 'email_subject': 'Reset your password'}
                logger.debug(f"Sending password reset email to {user.email}")
                Util.send_email(data)
                UserActivity.objects.create(user=user, action="Password reset requested")
                logger.info(f"Password reset email sent to {user.email}")
            return Response({'success': 'We have sent you a link to reset your password'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Password reset email request failed: {str(e)}")
            raise

class PasswordTokenCheckAPI(generics.GenericAPIView):
    def get(self, request, uidb64, token):
        logger.info("Checking password reset token")
        try:
            id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                logger.error(f"Invalid token for user {user.id}")
                return Response({'error': 'Token is not valid, please request a new one'}, status=status.HTTP_400_BAD_REQUEST)
            logger.info(f"Token validated for user {user.id}")
            return Response({'success': True, 'uidb64': uidb64, 'token': token}, status=status.HTTP_200_OK)
        except DjangoUnicodeDecodeError:
            logger.error("Invalid UID during token check")
            return Response({'error': 'Token is not valid, please request a new one'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Token check failed: {str(e)}")
            raise

class SetNewPasswordAPIView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def patch(self, request):
        logger.info("Starting password reset process")
        serializer = self.serializer_class(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data
            UserActivity.objects.create(user=user, action="Password reset completed")
            logger.info(f"Password reset completed for user {user.email}")
            return Response({'success': True, 'message': 'Password reset success'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Password reset failed: {str(e)}")
            raise

class LogoutAPIView(generics.GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        logger.info("Starting user logout process")
        serializer = self.serializer_class(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            UserActivity.objects.create(user=request.user, action="User logged out")
            logger.info(f"User {request.user.email} logged out successfully")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            raise

class UpdateProfileView(generics.UpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        logger.info(f"Starting profile update for user {request.user.email}")
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            UserActivity.objects.create(user=instance, action="Profile updated")
            logger.info(f"Profile updated successfully for user {instance.email}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Profile update failed: {str(e)}")
            raise

class SubscriptionStatusView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        logger.info(f"Fetching subscription status for user {request.user.email}")
        user = request.user
        try:
            if user.subscription_plan:
                data = {
                    'plan': user.subscription_plan.name,
                    'price': user.subscription_plan.price,
                    'duration_days': user.subscription_plan.duration_days,
                    'active': user.is_active
                }
                logger.info(f"Subscription status retrieved for user {user.email}")
                return Response(data, status=status.HTTP_200_OK)
            logger.info(f"No active subscription for user {user.email}")
            return Response({'message': 'No active subscription'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Subscription status fetch failed: {str(e)}")
            raise

class ReferralStatsView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        logger.info(f"Fetching referral stats for user {request.user.email}")
        user = request.user
        try:
            referral_count = user.referrals.count()
            data = {
                'referral_code': user.referral_code,
                'referral_count': referral_count,
                'credits_earned': referral_count * 10
            }
            logger.info(f"Referral stats retrieved for user {user.email}")
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Referral stats fetch failed: {str(e)}")
            raise

class Enable2FAView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        logger.info(f"Starting 2FA enable process for user {request.user.email}")
        user = request.user
        try:
            if not user.is_2fa_enabled:
                user.otp_secret = Util.generate_otp_secret()
                user.is_2fa_enabled = True
                user.save()
                totp = pyotp.TOTP(user.otp_secret)
                otp = totp.now()
                Util.send_otp(user.email, otp)
                UserActivity.objects.create(user=user, action="2FA enabled")
                logger.info(f"2FA enabled and OTP sent to {user.email}")
                return Response({'message': '2FA enabled, OTP sent'}, status=status.HTTP_200_OK)
            logger.error(f"2FA already enabled for user {user.email}")
            return Response({'error': '2FA already enabled'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"2FA enable failed: {str(e)}")
            raise

class VerifyOTPView(generics.GenericAPIView):
    serializer_class = OTPSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        logger.info(f"Starting OTP verification for user {request.user.email}")
        serializer = self.serializer_class(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            otp = serializer.validated_data['otp']
            user = request.user
            totp = pyotp.TOTP(user.otp_secret)
            if totp.verify(otp):
                UserActivity.objects.create(user=user, action="OTP verified")
                logger.info(f"OTP verified successfully for user {user.email}")
                return Response({'message': 'OTP verified'}, status=status.HTTP_200_OK)
            logger.error(f"Invalid OTP provided for user {user.email}")
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"OTP verification failed: {str(e)}")
            raise

class ActivityLogView(generics.ListAPIView):
    serializer_class = UserActivitySerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        logger.info(f"Fetching activity log for user {self.request.user.email}")
        return UserActivity.objects.filter(user=self.request.user)

class RequestEmailUpdate(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EmailUpdateRequestSerializer

    def post(self, request):
        logger.info(f"Starting email update request for user {request.user.email}")
        serializer = self.serializer_class(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = request.user
            current_email = user.email
            new_email = serializer.validated_data['new_email']

            if serializer.validated_data['current_email'] != current_email:
                logger.error(f"Email mismatch: Provided {serializer.validated_data['current_email']}, Expected {current_email}")
                return Response({"error": "Current email does not match your account."}, status=status.HTTP_400_BAD_REQUEST)

            logger.info(f"Email update requested: {current_email} -> {new_email}")
            user.temp_new_email = new_email
            user.save()
            logger.debug(f"temp_new_email set to {user.temp_new_email}")

            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = PasswordResetTokenGenerator().make_token(user)
            confirm_link = f"{settings.FRONTEND_URL}/email-update/confirm/?uidb64={uidb64}&token={token}"

            subject = "Confirm Your Email Update"
            message = (
                f"Hi {user.username},\n\n"
                f"You requested to update your email from {current_email} to {new_email}.\n"
                f"Click the link below to confirm:\n{confirm_link}\n\n"
                f"If you didn’t request this, please contact support."
            )

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[current_email],
                fail_silently=False,
            )
            logger.info(f"Confirmation email sent to {current_email}")
            return Response({"message": "Email update confirmation link has been sent to your current email."}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Email update request failed: {str(e)}")
            return Response({"error": "Failed to send email. Please try again later."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ConfirmEmailUpdate(APIView):
    serializer_class = EmailUpdateConfirmSerializer

    def post(self, request):
        logger.info("Starting email update confirmation process")
        serializer = self.serializer_class(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            uidb64 = serializer.validated_data['uidb64']
            token = serializer.validated_data['token']

            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)
            logger.debug(f"Confirming email update for user {user_id}. Current temp_new_email: {user.temp_new_email}")

            if not PasswordResetTokenGenerator().check_token(user, token):
                logger.error(f"Invalid or expired token for user {user_id}")
                return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

            if not user.temp_new_email:
                logger.error(f"No temp_new_email found for user {user_id}")
                return Response({"error": "No pending email update found."}, status=status.HTTP_400_BAD_REQUEST)

            old_email = user.email
            user.email = user.temp_new_email
            user.temp_new_email = None
            user.save()
            logger.info(f"Email updated for user {user_id}: {old_email} -> {user.email}")
            return Response({"message": "Email updated successfully."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            logger.error(f"User not found for uidb64: {uidb64}")
            return Response({"error": "Invalid user."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Email update confirmation failed: {str(e)}")
            return Response({"error": "Failed to update email. Please try again."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)