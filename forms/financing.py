from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from base.models.academic_year import AcademicYear

__all__ = [
    'FinancingFilterForm',
    'FinancingImportForm',
]


class FinancingFilterForm(forms.Form):
    year = forms.ModelChoiceField(
        label=_('academic_year'),
        queryset=AcademicYear.objects.all(),
        empty_label=_('current_year'),
        required=False,
    )


class FinancingImportForm(forms.Form):
    csv_file = forms.FileField(
        label=_('csv_file'),
        required=True,
    )
    import_academic_year = forms.ModelChoiceField(
        label=_('academic_year'),
        queryset=AcademicYear.objects.all(),
        empty_label=_('academic_years'),
        required=True,
    )

    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']
        if not csv_file.name.endswith('.csv'):
            raise ValidationError(_('financing_csv_file_invalid_extension'))
        return csv_file
