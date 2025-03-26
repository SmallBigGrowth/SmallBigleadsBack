from rest_framework import serializers
from .models import User, SubscriptionPlan, UserActivity
from django.contrib import auth
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework.exceptions import ValidationError

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=68, min_length=6, write_only=True)

    default_error_messages = {
        'username': 'The username should only contain alphanumeric characters'
    }

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'first_name', 'last_name']

    def validate(self, attrs):
        username = attrs.get('username', '')
        if not username.isalnum():
            raise serializers.ValidationError(self.default_error_messages)
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class EmailVerificationSerializer(serializers.ModelSerializer):
    token = serializers.CharField(max_length=555)

    class Meta:
        model = User
        fields = ['token']

class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255, min_length=3)
    password = serializers.CharField(max_length=68, min_length=6, write_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    subscription_plan = serializers.SlugRelatedField(slug_field='name', read_only=True)
    referred_by = serializers.SlugRelatedField(slug_field='email', read_only=True)
    tokens = serializers.SerializerMethodField()

    def get_tokens(self, obj):
        return obj.tokens()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'first_name', 'last_name', 'auth_provider',
            'is_verified', 'credits', 'subscription_plan', 'referral_code', 'referred_by',
            'third_party_verified', 'third_party_response', 'is_active', 'is_staff',
            'created_at', 'updated_at', 'profile_picture', 'bio', 'phone_number',
            'is_2fa_enabled', 'otp_secret', 'tokens'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'otp_secret': {'write_only': True},
            'id': {'read_only': True},
            'auth_provider': {'read_only': True},
            'is_verified': {'read_only': True},
            'credits': {'read_only': True},
            'subscription_plan': {'read_only': True},
            'referral_code': {'read_only': True},
            'referred_by': {'read_only': True},
            'third_party_verified': {'read_only': True},
            'third_party_response': {'read_only': True},
            'is_active': {'read_only': True},
            'is_staff': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
            'profile_picture': {'read_only': True},
            'bio': {'read_only': True},
            'phone_number': {'read_only': True},
            'is_2fa_enabled': {'read_only': True},
        }

    def validate(self, attrs):
        email = attrs.get('email', '')
        password = attrs.get('password', '')
        user = auth.authenticate(email=email, password=password)
        if not user:
            raise AuthenticationFailed('Invalid credentials, try again')
        if not user.is_active:
            raise AuthenticationFailed('Account disabled, contact admin')
        if not user.is_verified:
            raise AuthenticationFailed('Email is not verified')
        return self.to_representation(user)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tokens'] = instance.tokens()
        return representation

class ResetPasswordEmailRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=2)
    redirect_url = serializers.CharField(max_length=500, required=False)

    class Meta:
        fields = ['email']

class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=6, max_length=68, write_only=True)
    token = serializers.CharField(min_length=1, write_only=True)
    uidb64 = serializers.CharField(min_length=1, write_only=True)

    class Meta:
        fields = ['password', 'token', 'uidb64']

    def validate(self, attrs):
        try:
            password = attrs.get('password')
            token = attrs.get('token')
            uidb64 = attrs.get('uidb64')
            id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed('The reset link is invalid', 401)
            user.set_password(password)
            user.save()
            return user
        except Exception:
            raise AuthenticationFailed('The reset link is invalid', 401)

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    error_messages = {
        'bad_token': 'Token is expired, invalid, or already blacklisted',
    }

    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):
        try:
            token = RefreshToken(self.token)
            token.blacklist()  
        except TokenError as e:
            raise ValidationError({'refresh': self.error_messages['bad_token']})

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'profile_picture', 'bio', 'phone_number']

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['name', 'price', 'duration_days']

class OTPSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6)

class UserActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivity
        fields = ['action', 'timestamp']

from rest_framework import serializers
from .models import User

class EmailUpdateRequestSerializer(serializers.Serializer):
    current_email = serializers.EmailField(min_length=2)
    new_email = serializers.EmailField(min_length=2)

    def validate(self, attrs):
        current_email = attrs.get('current_email')
        new_email = attrs.get('new_email')
        if current_email == new_email:
            raise serializers.ValidationError("New email must be different from the current email.")
        if User.objects.filter(email=new_email).exists():
            raise serializers.ValidationError("This new email is already in use.")
        return attrs

class EmailUpdateConfirmSerializer(serializers.Serializer):
    uidb64 = serializers.CharField(min_length=1)
    token = serializers.CharField(min_length=1)