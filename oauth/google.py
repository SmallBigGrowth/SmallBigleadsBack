from google.auth.transport import requests
from google.oauth2 import id_token
import os
from decouple import config

class Google:
    @staticmethod
    def validate(auth_token):
        try:
            idinfo = id_token.verify_oauth2_token(
                auth_token, requests.Request(),config("GOOGLE_CLIENT_ID"))

            if 'accounts.google.com' in idinfo['iss']:
                return idinfo
        except:
            return None