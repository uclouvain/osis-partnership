from django import forms
from django.db.models import F, Subquery

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
        qs = AcademicYear.objects.annotate(
            current_year=Subquery(AcademicYear.objects.currents().values('year')[:1]),
        ).filter(
            year__gte=F('current_year'),
            year__lte=F('current_year') + 2,
        )
        self.fields['partnership_creation_update_min_year'].queryset = qs
        self.fields['partnership_api_year'].queryset = qs
