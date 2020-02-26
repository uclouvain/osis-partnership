from django import forms
from django.utils.translation import gettext_lazy as _

__all__ = ['CustomNullBooleanSelect']


class CustomNullBooleanSelect(forms.NullBooleanSelect):
    def __init__(self, attrs=None):
        choices = (
            ('1', '---------'),
            ('2', _('Yes')),
            ('3', _('No')),
        )
        super(forms.NullBooleanSelect, self).__init__(attrs, choices)
