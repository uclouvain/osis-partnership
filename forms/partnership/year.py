from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear
from base.models.entity import Entity
from partnership.models import (
    Partnership, PartnershipConfiguration, PartnershipYear,
)
from partnership.utils import user_is_adri
from ..fields import (
    EducationGroupYearChoiceSelect, EntityChoiceMultipleField,
)

__all__ = ['PartnershipYearForm']


class PartnershipYearForm(forms.ModelForm):
    # Used for the dal forward
    faculty = forms.CharField(required=False, widget=forms.HiddenInput())

    start_academic_year = forms.ModelChoiceField(
        label=_('start_academic_year'),
        queryset=AcademicYear.objects.all(),
        required=True,
    )
    from_academic_year = forms.ModelChoiceField(
        label=_('from_academic_year'),
        queryset=AcademicYear.objects.all(),
        required=True,
    )
    end_academic_year = forms.ModelChoiceField(
        label=_('end_academic_year'),
        queryset=AcademicYear.objects.all(),
        required=True,
    )

    entities = EntityChoiceMultipleField(
        label=_('partnership_year_entities'),
        help_text=_('partnership_year_entities_help_text'),
        queryset=Entity.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
            url='partnerships:autocomplete:partnership_year_entities',
            forward=['faculty'],
        ),
    )

    offers = EducationGroupYearChoiceSelect(
        label=_('partnership_year_offers'),
        help_text=_('partnership_year_offers_help_text'),
        queryset=EducationGroupYear.objects.filter(joint_diploma=True),
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
            url='partnerships:autocomplete:partnership_year_offers',
            forward=['faculty', 'entities', 'education_levels'],
        ),
    )

    class Meta:
        model = PartnershipYear
        fields = (
            'partnership_type',
            'education_fields',
            'education_levels',
            'entities',
            'offers',
            'is_sms',
            'is_smp',
            'is_smst',
            'is_sta',
            'is_stt',
            'eligible',
        )
        widgets = {
            'education_fields': autocomplete.ModelSelect2Multiple(),
            'education_levels': autocomplete.ModelSelect2Multiple(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['partnership_type'].initial = PartnershipYear.TYPE_MOBILITY
        self.fields['partnership_type'].disabled = True
        current_academic_year = (
            PartnershipConfiguration.get_configuration().get_current_academic_year_for_creation_modification()
        )
        is_adri = user_is_adri(self.user)
        if not is_adri:
            del self.fields['eligible']
            if current_academic_year is not None:
                future_academic_years = AcademicYear.objects.filter(year__gte=current_academic_year.year)
                self.fields['start_academic_year'].queryset = future_academic_years
                self.fields['from_academic_year'].queryset = future_academic_years
                self.fields['end_academic_year'].queryset = future_academic_years
        try:
            # Update
            if (current_academic_year is not None
                    and current_academic_year.year > self.instance.partnership.end_academic_year.year):
                self.fields['end_academic_year'].initial = current_academic_year
            else:
                self.fields['end_academic_year'].initial = self.instance.partnership.end_academic_year
            if is_adri:
                self.fields['start_academic_year'].initial = self.instance.partnership.start_academic_year
            else:
                del self.fields['start_academic_year']
            self.fields['from_academic_year'].initial = current_academic_year
        except Partnership.DoesNotExist:
            # Create
            self.fields['start_academic_year'].initial = current_academic_year
            del self.fields['from_academic_year']
            self.fields['end_academic_year'].initial = current_academic_year

    def clean(self):
        super().clean()
        if self.cleaned_data['is_sms'] or self.cleaned_data['is_smp']:
            if not self.cleaned_data['education_levels']:
                self.add_error(
                    'education_levels',
                    ValidationError(_('education_levels_empty_errors')),
                )
        else:
            self.cleaned_data['education_levels'] = []
            self.cleaned_data['entities'] = []
            self.cleaned_data['offers'] = []
        start_academic_year = self.cleaned_data.get('start_academic_year', None)
        from_academic_year = self.cleaned_data.get('from_academic_year', None)
        end_academic_year = self.cleaned_data.get('end_academic_year', None)
        if start_academic_year is not None:
            if start_academic_year.year > end_academic_year.year:
                self.add_error(
                    'start_academic_year',
                    ValidationError(_('start_date_after_end_date')),
                )
            if from_academic_year is not None and start_academic_year.year > from_academic_year.year:
                self.add_error(
                    'start_academic_year',
                    ValidationError(_('start_date_after_from_date')),
                )
        if from_academic_year is not None and from_academic_year.year > end_academic_year.year:
            self.add_error(
                'from_academic_year',
                ValidationError(_('from_date_after_end_date')),
            )
        return self.cleaned_data
