from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from base.forms.utils.datefield import DATE_FORMAT, DatePickerInput
from base.models.academic_year import find_academic_years
from partnership.auth.predicates import is_linked_to_adri_entity
from partnership.models import PartnershipAgreement, PartnershipType

__all__ = ['PartnershipAgreementForm']


class PartnershipAgreementForm(forms.ModelForm):

    class Meta:
        model = PartnershipAgreement
        fields = [
            'start_academic_year',
            'end_academic_year',
            'start_date',
            'end_date',
            'status',
            'comment',
        ]
        widgets = {
            'start_date': DatePickerInput(
                format=DATE_FORMAT,
                attrs={
                    'class': 'datepicker',
                    'placeholder': _('partnership_start_date'),
                    'autocomplete': 'off',
                },
            ),
            'end_date': DatePickerInput(
                format=DATE_FORMAT,
                attrs={
                    'class': 'datepicker',
                    'placeholder': _('partnership_end_date'),
                    'autocomplete': 'off',
                },
            ),
        }

    def __init__(self, user=None, partnership=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not is_linked_to_adri_entity(user):
            del self.fields['status']

        if partnership.partnership_type in [
            PartnershipType.GENERAL.name,
            PartnershipType.COURSE.name,
            PartnershipType.DOCTORATE.name,
        ]:
            del self.fields['start_academic_year']
            del self.fields['end_academic_year']
        else:
            del self.fields['start_date']
            del self.fields['end_date']

    def clean(self):
        super().clean()
        data = self.cleaned_data
        start_academic_year = data.get('start_academic_year', None)
        end_academic_year = data.get('end_academic_year', None)
        if (start_academic_year is not None and end_academic_year is not None
                and start_academic_year.year > end_academic_year.year):
            self.add_error('start_academic_year', ValidationError(_('start_date_after_end_date')))
            self.add_error('end_academic_year', ValidationError(_('start_date_after_end_date')))

        # Sync date fields
        if start_academic_year is not None and end_academic_year is not None:
            data['start_date'] = start_academic_year.start_date
            data['end_date'] = start_academic_year.end_date
        else:
            years = find_academic_years(
                # We need academic years surrounding this time range
                start_date=data['end_date'],
                end_date=data['start_date'],
            )
            data['start_academic_year'] = years.first()
            data['end_academic_year'] = years.last()

        return data
