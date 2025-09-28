# custom_auth_backend.py
from django.contrib.auth.backends import ModelBackend
from .models import Account  # Import your custom user model

class CustomBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Use your custom user model for authentication
            user = Account.objects.get(username=username)
        except Account.DoesNotExist:
            return None

        if user.check_password(password):
            return user
        return None
