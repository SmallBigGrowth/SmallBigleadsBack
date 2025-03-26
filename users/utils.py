from django.core.mail import EmailMessage
import threading
import pyotp

class EmailThread(threading.Thread):
    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send()

class Util:
    @staticmethod
    def send_email(data):
        email = EmailMessage(
            subject=data['email_subject'], body=data['email_body'], to=[data['to_email']])
        EmailThread(email).start()

    @staticmethod
    def generate_otp_secret():
        return pyotp.random_base32()

    @staticmethod
    def send_otp(email, otp):
        email_body = f'Your OTP is {otp}. It is valid for 5 minutes.'
        data = {'email_body': email_body, 'to_email': email, 'email_subject': 'Your OTP'}
        Util.send_email(data)