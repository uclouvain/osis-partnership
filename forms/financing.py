from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from base.models.academic_year import AcademicYear
from partnership.models import FundingType

__all__ = [
    'FinancingFilterForm',
    'FinancingImportForm',
    'FundingUpdateFormMixin',
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


class FundingUpdateFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Disable the is_active if parent is inactive
        if isinstance(self.instance, FundingType) and not self.instance.program.is_active:
            self.fields['is_active'].disabled = True
            self.fields['is_active'].help_text = _(
                "This funding type can not be enabled as its parent is not active."
            )
