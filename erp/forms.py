from django import forms
from django.contrib.auth.models import User


class LoginForm(forms.Form):
    username = forms.CharField(max_length=100, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)

from django import forms
from django.contrib.auth.models import User

class RegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=100, required=True, label='First Name')
    last_name = forms.CharField(max_length=100, required=True, label='Last Name')
    email = forms.EmailField(max_length=100, required=True, label='Email Address')
    user_name = forms.CharField(max_length=100, required=True, label='User Name')
    password = forms.CharField(widget=forms.PasswordInput, required=True, label='Password')
    password_confirmation = forms.CharField(widget=forms.PasswordInput, required=True, label='Confirm Password')

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirmation = cleaned_data.get("password_confirmation")
        
        if password and password_confirmation:
            if password != password_confirmation:
                raise forms.ValidationError("Passwords do not match.")
        return cleaned_data
