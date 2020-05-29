from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear
from base.models.entity import Entity
from partnership.auth.predicates import is_linked_to_adri_entity
from partnership.models import (
    PartnershipConfiguration, PartnershipYear,
)
from ..fields import (
    EducationGroupYearChoiceSelect, EntityChoiceMultipleField,
)

__all__ = [
    'PartnershipYearGeneralForm',
    'PartnershipYearMobilityForm',
    'PartnershipYearCourseForm',
    'PartnershipYearDoctorateForm',
    'PartnershipYearProjectForm',
]


class PartnershipYearBaseForm(forms.ModelForm):
    # Used for the dal forward
    entity = forms.CharField(required=False, widget=forms.HiddenInput())

    entities = EntityChoiceMultipleField(
        label=_('partnership_year_entities'),
        help_text=_('partnership_year_entities_help_text'),
        queryset=Entity.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
            url='partnerships:autocomplete:partnership_year_entities',
            forward=['entity'],
        ),
    )

    offers = EducationGroupYearChoiceSelect(
        label=_('partnership_year_offers'),
        help_text=_('partnership_year_offers_help_text'),
        queryset=EducationGroupYear.objects.filter(joint_diploma=True),
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
            url='partnerships:autocomplete:partnership_year_offers',
            forward=['entity', 'entities', 'education_levels'],
        ),
    )

    class Meta:
        model = PartnershipYear
        fields = (
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
            'funding_type',
        )
        widgets = {
            'education_fields': autocomplete.ModelSelect2Multiple(),
            'education_levels': autocomplete.ModelSelect2Multiple(),
            'eligible': forms.HiddenInput(),
        }

    def __init__(self, partnership_type=None, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.partnership_type = partnership_type
        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()
        data = self.cleaned_data

        if data['is_sms'] or data['is_smp']:
            if not data['education_levels']:
                self.add_error(
                    'education_levels',
                    ValidationError(_('education_levels_empty_errors')),
                )
        else:
            data['education_levels'] = []
            data['entities'] = []
            data['offers'] = []

        return data


class PartnershipYearWithoutDatesForm(PartnershipYearBaseForm):
    """
    The duration of the partnership is encoded through academic_years
    """
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

    def clean(self):
        super().clean()
        data = self.cleaned_data

        start_academic_year = data.get('start_academic_year', None)
        from_academic_year = data.get('from_academic_year', None)
        end_academic_year = data.get('end_academic_year', None)
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
        return data


class PartnershipYearGeneralForm(PartnershipYearBaseForm):
    pass


class PartnershipYearMobilityForm(PartnershipYearWithoutDatesForm):
    class Meta(PartnershipYearBaseForm.Meta):
        fields = PartnershipYearBaseForm.Meta.fields + (
            'funding_type',
        )
        widgets = {
            **PartnershipYearBaseForm.Meta.widgets,
            'funding_type': autocomplete.ModelSelect2(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['funding_type'].help_text = _('help_text_funding_type')
        self.fields['funding_type'].required = False

        self.fields['eligible'].widget = forms.CheckboxInput()

        is_adri = is_linked_to_adri_entity(self.user)

        config = PartnershipConfiguration.get_configuration()
        current_academic_year = config.partnership_creation_update_min_year
        if not is_adri:
            del self.fields['eligible']

            if current_academic_year is not None:
                future_academic_years = AcademicYear.objects.filter(
                    year__gte=current_academic_year.year
                )
                self.fields['start_academic_year'].queryset = future_academic_years
                self.fields['from_academic_year'].queryset = future_academic_years
                self.fields['end_academic_year'].queryset = future_academic_years

        if self.instance.partnership_id:
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
        else:
            # Create
            self.fields['start_academic_year'].initial = current_academic_year
            del self.fields['from_academic_year']
            self.fields['end_academic_year'].initial = current_academic_year


class PartnershipYearCourseForm(PartnershipYearBaseForm):
    pass


class PartnershipYearDoctorateForm(PartnershipYearBaseForm):
    pass


class PartnershipYearProjectForm(PartnershipYearBaseForm):
    class Meta(PartnershipYearBaseForm.Meta):
        fields = PartnershipYearBaseForm.Meta.fields + (
            'funding_type',
        )
        widgets = {
            **PartnershipYearBaseForm.Meta.widgets,
            'funding_type': autocomplete.ModelSelect2(),
        }
