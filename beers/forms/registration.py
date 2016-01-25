
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
import re

class ProfileForm(forms.Form):
    "Form for editing a profile"
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    personal_statement = forms.CharField(max_length=150, widget=forms.Textarea,
        required=False, label='Motto')
    untappd_username = forms.CharField(max_length=150, required=True,
            label="Untappd Username")
    untappd_rss = forms.URLField(max_length=512, required=True,
            label="Untappd RSS Link",
            help_text="Copy the URL from your Untappd account page")

class RegistrationForm(ProfileForm):
    "Form for registering a new user, including profile data"

    username = forms.CharField(max_length=30, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    password_repeat = forms.CharField(widget=forms.PasswordInput, required=True)

    re_username = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]{5,29}$')

    def clean_username(self):
        if not re.match(RegistrationForm.re_username, self.cleaned_data['username']):
            raise forms.ValidationError('Username must start with a character and can only contain letters, numbers and underscores', code='username_valid')
        if User.objects.filter(username=self.cleaned_data['username']).count() > 0:
            raise forms.ValidationError('Username already taken', code='username_taken')
        return self.cleaned_data['username']

    def clean(self):
        super(RegistrationForm, self).clean()
        if self.cleaned_data['password'] != self.cleaned_data['password_repeat']:
            self.add_error('password', forms.ValidationError('Passwords must match', code='password_match'))
        try:
            validate_password(self.cleaned_data['password'])
        except forms.ValidationError as e:
            self.add_error('password', e)
        return self.cleaned_data
