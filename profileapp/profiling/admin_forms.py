from django import forms
from django.contrib.auth.hashers import make_password, identify_hasher
from .models import Account

class AccountAdminForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ('username', 'email', 'password', 'is_verified', 'join_date', 'is_staff', 'is_active')

    def clean_password(self):
        password = self.cleaned_data.get("password")

        # If already hashed (starts with algorithm prefix), return as-is
        try:
            identify_hasher(password)
            return password  # Already hashed
        except Exception:
            return make_password(password)  # Hash raw password
