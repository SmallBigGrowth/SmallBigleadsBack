from rest_framework import serializers
from .utils import register_social_user
from .google import Google
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.exceptions import ValidationError
import logging
from decouple import config

logger = logging.getLogger(__name__)

class GoogleSocialAuthSerializer(serializers.Serializer):
    auth_token = serializers.CharField(write_only=True)

    def validate_auth_token(self, auth_token):
        logger.info("Starting token validation for Google social auth")
        
        try:
            user_data = Google.validate(auth_token)
            logger.debug(f"Received user data: {user_data}")
            
            if not user_data:
                logger.error("Token validation failed: invalid or expired token")
                raise serializers.ValidationError('The token is invalid or expired. Please login again.')

            expected_client_id =config("GOOGLE_CLIENT_ID")
            if user_data['aud'] != expected_client_id:
                logger.error(f"Invalid client ID. Expected: {expected_client_id}, Got: {user_data['aud']}")
                raise AuthenticationFailed('Invalid client ID.')

            user_id = user_data['sub']
            email = user_data['email']
            name = user_data.get('name', '')
            provider = 'google'

            logger.info(f"Successfully validated token for user: {email}")
            logger.debug(f"User details - ID: {user_id}, Name: {name}, Provider: {provider}")

            result = register_social_user(provider, user_id, email, name)
            logger.info(f"User registration completed for {email}")
            
            return result

        except Exception as e:
            logger.exception(f"Unexpected error during token validation: {str(e)}")
            raise