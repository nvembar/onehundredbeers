import autocomplete_light.shortcuts as al
from .models import Contest_Beer

al.register(Contest_Beer,
    search_fields=['beer__name', 'beer__brewery'],
    attrs={
        'placeholder': 'Search for beer',
        'data-autocomplete-minimum-characters': 1,
    },
    widget_attrs={
        'data-widget-maximum-values': 4,
        'class': 'modern-style',
    },
)
