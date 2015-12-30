from django import forms
from beers.models import Contest
import re

class ContestForm(forms.Form):
    "Form for creating a new contest"

    name = forms.CharField(max_length=250)
    start_date = forms.DateField()
    end_date = forms.DateField()
    re_name = re.compile('^[A-Za-z][A-Za-z0-9_\- ]{0,249}$')

    def clean_name(self):
        name = self.cleaned_data['name']
        if not re.match(ContestForm.re_name, name):
            raise forms.ValidationError('Contest name must start with an alphabetic character and can only contain letters, numbers, spaces and underscores', code='contest_name_valid')
        if Contest.objects.filter(name=name).count() > 0:
            raise forms.ValidationError('Contest name "{0}" already taken'.format(name))
        return name
