import random
from users.models import User
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import authenticate
import os
from rest_framework_simplejwt.tokens import RefreshToken
from decouple import config

def generate_username(name):
    username = "".join(name.split(' ')).lower()
    if not User.objects.filter(username=username).exists():
        return username
    else:
        random_username = username + str(random.randint(0, 1000))
        return generate_username(random_username)

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

def register_social_user(provider, user_id, email, name):
    filtered_user_by_email = User.objects.filter(email=email)

    if filtered_user_by_email.exists():
        registered_user = filtered_user_by_email[0]
        if provider != registered_user.auth_provider:
            raise AuthenticationFailed(
                detail=f'Please continue your login using {registered_user.auth_provider}')
        subscription_data = None
        if registered_user.subscription_plan:
            subscription_data = {
                'name': registered_user.subscription_plan.name,
                'price': str(registered_user.subscription_plan.price),
                'duration_days': registered_user.subscription_plan.duration_days
            }
        return {
            'id': str(registered_user.id),
            'username': registered_user.username,
            'email': registered_user.email,
            'first_name': registered_user.first_name,
            'last_name': registered_user.last_name,
            'credits': registered_user.credits,
            'referral_code': registered_user.referral_code,
            'is_verified': registered_user.is_verified,
            'auth_provider': registered_user.auth_provider,
            'subscription_plan': subscription_data,
            'third_party_verified': registered_user.third_party_verified,
            'third_party_response': registered_user.third_party_response,
            'is_active': registered_user.is_active,
            'is_staff': registered_user.is_staff,
            'created_at': registered_user.created_at.isoformat(),
            'updated_at': registered_user.updated_at.isoformat(),
            'profile_picture': str(registered_user.profile_picture) if registered_user.profile_picture else None,
            'bio': registered_user.bio,
            'phone_number': registered_user.phone_number,
            'is_2fa_enabled': registered_user.is_2fa_enabled,
            'tokens': get_tokens_for_user(registered_user)
        }
    else:
        user = User.objects.create_user(
            username=generate_username(name),
            email=email,
            password=config("GOOGLE_SEC_ID"),  
            first_name=name.split(' ')[0] if ' ' in name else name,
            last_name=name.split(' ')[-1] if ' ' in name else ''
        )
        user.is_verified = True
        user.auth_provider = provider
        user.save()
        subscription_data = None
        if user.subscription_plan:
            subscription_data = {
                'name': user.subscription_plan.name,
                'price': str(user.subscription_plan.price),
                'duration_days': user.subscription_plan.duration_days
            }

        return {
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'credits': user.credits,
            'referral_code': user.referral_code,
            'is_verified': user.is_verified,
            'auth_provider': user.auth_provider,
            'subscription_plan': subscription_data,
            'third_party_verified': user.third_party_verified,
            'third_party_response': user.third_party_response,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'created_at': user.created_at.isoformat(),
            'updated_at': user.updated_at.isoformat(),
            'profile_picture': str(user.profile_picture) if user.profile_picture else None,
            'bio': user.bio,
            'phone_number': user.phone_number,
            'is_2fa_enabled': user.is_2fa_enabled,
            'tokens': get_tokens_for_user(user)
        }
