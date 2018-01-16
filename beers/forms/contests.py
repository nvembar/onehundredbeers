from django import forms
from django.utils import timezone
from django.utils import html
from beers.models import Contest, Contest_Beer
import datetime
import re


class SubmitButtonWidget(forms.Widget):
    def render(self, name, value, attrs=None):
        return '<input type="submit" name="%s" value="%s">' % (html.escape(name), html.escape(value))

class SubmitButtonField(forms.Field):
    def __init__(self, *args, **kwargs):
        if not kwargs:
            kwargs = {}
        kwargs["widget"] = SubmitButtonWidget

        super(SubmitButtonField, self).__init__(*args, **kwargs)

    def clean(self, value):
        return value


class ContestForm(forms.Form):
    "Form for creating a new contest"

    name = forms.CharField(max_length=250, 
            widget=forms.TextInput(attrs={'class': 'form-control'}))
    start_date = forms.DateField(
            widget=forms.TextInput(attrs={'class': 'form-control datepicker',
                                          'data-provide': 'datepicker'}))
    end_date = forms.DateField(
            widget=forms.TextInput(attrs={'class': 'form-control datepicker',
                                          'data-provide': 'datepicker'}))
    re_name = re.compile('^[A-Za-z][A-Za-z0-9_\-\'"\.\! ]{0,249}$')

    def clean_name(self):
        """Ensure that the name is rational and unique"""
        name = self.cleaned_data['name']
        if not re.match(ContestForm.re_name, name):
            raise forms.ValidationError(
                'Contest name must start with an alphabetic character ' +
                'and can only contain letters, numbers, spaces, periods, quotes ' +
                'and underscores', code='contest_name_valid')
        if Contest.objects.filter(name=name).count() > 0:
            raise forms.ValidationError('Contest name "{0}" already taken'.format(name))
        return name

    def clean_end_date(self):
        """Makes the end date a time at the very end of the day"""
        dt = datetime.datetime.combine(self.cleaned_data['end_date'], datetime.time(23, 59, 59))
        return timezone.make_aware(dt)

    def clean_start_date(self):
        """Makes the start date a time starting at midnight"""
        dt = datetime.datetime.combine(self.cleaned_data['start_date'], datetime.time())
        return timezone.make_aware(dt)

    def clean(self):
        super(ContestForm, self).clean()
        if self.cleaned_data['start_date'] >= self.cleaned_data['end_date']:
            self.add_error('start_date', forms.ValidationError('Start date ' +
                    'must be before end date', code='date_compare'))
        return self.cleaned_data
