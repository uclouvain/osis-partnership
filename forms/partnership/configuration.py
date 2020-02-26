from datetime import date

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from partnership.models import PartnershipConfiguration

__all__ = ['PartnershipConfigurationForm']


class PartnershipConfigurationForm(forms.ModelForm):

    class Meta:
        model = PartnershipConfiguration
        fields = [
            'partnership_creation_update_max_date_day',
            'partnership_creation_update_max_date_month',
            'partnership_api_max_date_day',
            'partnership_api_max_date_month',
            'email_notification_to',
        ]

    def clean(self):
        super().clean()
        try:
            date(
                2001,
                self.cleaned_data['partnership_creation_update_max_date_month'],
                self.cleaned_data['partnership_creation_update_max_date_day'],
            )
        except ValueError:
            self.add_error(
                'partnership_creation_update_max_date_day',
                ValidationError(_('invalid_partnership_creation_max_date'))
            )
        try:
            date(
                2001,
                self.cleaned_data['partnership_api_max_date_month'],
                self.cleaned_data['partnership_api_max_date_day'],
            )
        except ValueError:
            self.add_error(
                'partnership_api_max_date_day',
                ValidationError(_('invalid_partnership_api_max_date'))
            )
        return self.cleaned_data
