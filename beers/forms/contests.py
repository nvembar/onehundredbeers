from django import forms
from django.utils import timezone
from beers.models import Contest
import datetime
import re

class ContestForm(forms.Form):
    "Form for creating a new contest"

    name = forms.CharField(max_length=250)
    start_date = forms.DateField()
    end_date = forms.DateField()
    re_name = re.compile('^[A-Za-z][A-Za-z0-9_\- ]{0,249}$')

    def clean_name(self):
        """Ensure that the name is rational and unique"""
        name = self.cleaned_data['name']
        if not re.match(ContestForm.re_name, name):
            raise forms.ValidationError('Contest name must start with an alphabetic character and can only contain letters, numbers, spaces and underscores', code='contest_name_valid')
        if Contest.objects.filter(name=name).count() > 0:
            raise forms.ValidationError('Contest name "{0}" already taken'.format(name))
        return name

    def clean_end_date(self):
        """Makes the end date a time at the very end of the day"""
        return datetime.datetime.combine(self.cleaned_data['end_date'], datetime.time(23, 59, 59))

    def clean_start_date(self):
        """Makes the start date a time starting at midnight"""
        return datetime.datetime.combine(self.cleaned_data['start_date'], datetime.time())
