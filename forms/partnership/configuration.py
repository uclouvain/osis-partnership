from datetime import date

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from base.models.academic_year import AcademicYear
from partnership.models import PartnershipConfiguration

__all__ = ['PartnershipConfigurationForm']


class PartnershipConfigurationForm(forms.ModelForm):

    class Meta:
        model = PartnershipConfiguration
        fields = [
            'partnership_creation_update_min_year',
            'partnership_api_year',
            'email_notification_to',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_year = date.today().year
        qs = AcademicYear.objects.filter(
            year__gte=current_year,
            year__lte=current_year + 2,
        )
        self.fields['partnership_creation_update_min_year'].queryset = qs
        self.fields['partnership_api_year'].queryset = qs
