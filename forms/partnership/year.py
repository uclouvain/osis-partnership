from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear
from base.models.entity import Entity
from partnership.auth.predicates import is_linked_to_adri_entity
from partnership.models import (
    Partnership, PartnershipConfiguration, PartnershipYear,
)
from ..fields import (
    EducationGroupYearChoiceSelect, EntityChoiceMultipleField,
)

__all__ = ['PartnershipYearForm']


class PartnershipYearForm(forms.ModelForm):
    # Used for the dal forward
    entity = forms.CharField(required=False, widget=forms.HiddenInput())

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
            'funding_type': forms.HiddenInput(),
        }

    def __init__(self, partnership_type=None, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        # Dynamically process form given partnership type
        if hasattr(self, 'process_' + partnership_type.lower()):
            getattr(self, 'process_' + partnership_type.lower())()

        current_academic_year = (
            PartnershipConfiguration.get_configuration().get_current_academic_year_for_creation_modification()
        )
        # FIXME what to do of the following when not mobility?
        is_adri = is_linked_to_adri_entity(self.user)
        if not is_adri:
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

    def process_mobility(self):
        """
        Process form for PartnershipType.MOBILITY
        """
        self.fields['eligible'].widget = forms.CheckboxInput()
        self.fields['funding_type'].widget = autocomplete.ModelSelect2()
        self.fields['funding_type'].help_text = _('help_text_funding_type')
        self.fields['funding_type'].required = False

        if not is_linked_to_adri_entity(self.user):
            del self.fields['eligible']

    def process_project(self):
        """
        Process form for PartnershipType.PROJECT
        """
        self.fields['funding_type'].widget = autocomplete.ModelSelect2(
            choices=self.fields['funding_type'].choices
        )

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
