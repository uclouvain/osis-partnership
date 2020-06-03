from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from base.forms.utils.datefield import DATE_FORMAT, DatePickerInput
from base.models.academic_year import find_academic_years
from partnership.auth.predicates import is_linked_to_adri_entity
from partnership.models import PartnershipAgreement

__all__ = [
    'PartnershipAgreementWithDatesForm',
    'PartnershipAgreementWithAcademicYearsForm',
]


class PartnershipAgreementFormMixin(forms.ModelForm):
    class Meta:
        model = PartnershipAgreement
        fields = [
            'start_date',
            'end_date',
            'start_academic_year',
            'end_academic_year',
            'status',
            'comment',
        ]

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not is_linked_to_adri_entity(user):
            del self.fields['status']


class PartnershipAgreementWithDatesForm(PartnershipAgreementFormMixin):
    class Meta(PartnershipAgreementFormMixin.Meta):
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

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        del self.fields['start_academic_year']
        del self.fields['end_academic_year']

    def clean(self):
        super().clean()
        years = find_academic_years(
            # We need academic years surrounding this time range
            start_date=self.cleaned_data['end_date'],
            end_date=self.cleaned_data['start_date'],
        )
        self.cleaned_data['start_academic_year'] = years.first()
        self.cleaned_data['end_academic_year'] = years.last()

        return self.cleaned_data


class PartnershipAgreementWithAcademicYearsForm(PartnershipAgreementFormMixin):
    def __init__(self, user=None, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        del self.fields['start_date']
        del self.fields['end_date']

    def clean(self):
        super().clean()
        data = self.cleaned_data
        start_academic_year = data.get('start_academic_year', None)
        end_academic_year = data.get('end_academic_year', None)
        if (start_academic_year and end_academic_year
                and start_academic_year.year > end_academic_year.year):
            self.add_error(
                'start_academic_year',
                ValidationError(_('start_date_after_end_date')),
            )
            self.add_error(
                'end_academic_year',
                ValidationError(_('start_date_after_end_date')),
            )

        # Sync date fields
        if start_academic_year is not None and end_academic_year is not None:
            data['start_date'] = start_academic_year.start_date
            data['end_date'] = start_academic_year.end_date

        return data
