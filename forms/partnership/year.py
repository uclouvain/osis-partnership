from dal import autocomplete
from dal.forward import Const
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear
from base.models.entity import Entity
from base.models.enums.education_group_types import TrainingType
from base.models.enums.entity_type import DOCTORAL_COMMISSION
from partnership.auth.predicates import is_linked_to_adri_entity
from partnership.models import (
    PartnershipConfiguration,
    PartnershipType, PartnershipYear,
    PartnershipYearEducationLevel,
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
    partnership_type = forms.CharField(required=False, widget=forms.HiddenInput())

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
            'eligible',
            'missions',
        )
        widgets = {
            'education_fields': autocomplete.ModelSelect2Multiple(),
            'education_levels': autocomplete.ModelSelect2Multiple(),
            'eligible': forms.HiddenInput(),
            'missions': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, partnership_type=None, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.partnership_type = partnership_type
        super().__init__(*args, **kwargs)

        # Fill the missions field according to the current type
        field_missions = self.fields['missions']
        field_missions.queryset = field_missions.queryset.filter(
            types__contains=[self.partnership_type],
        )
        # If only one mission available, force it
        if len(field_missions.queryset) == 1:
            field_missions.initial = [field_missions.queryset.first().pk]
            field_missions.widget = forms.MultipleHiddenInput()


class PartnershipYearSubtypeMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field_subtype = self.fields['subtype']

        # Constraint according to partnership type
        condition = Q(types__contains=[self.partnership_type])

        # Allow inactive types already set only for update
        if not self.instance.pk:
            condition &= (Q(is_active=True) | Q(pk=self.instance.subtype_id))
        else:
            condition &= Q(is_active=True)
        field_subtype.queryset = field_subtype.queryset.filter(condition)

        # Prevent empty value from showing
        field_subtype.empty_label = None


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

    def __init__(self, partnership_type=None, *args, **kwargs):
        super().__init__(partnership_type, *args, **kwargs)

        config = PartnershipConfiguration.get_configuration()
        current_academic_year = config.partnership_creation_update_min_year

        is_adri = is_linked_to_adri_entity(self.user)
        if self.instance.partnership_id:
            # Update
            partnership = self.instance.partnership
            if (current_academic_year is not None
                    and current_academic_year.year > partnership.end_academic_year.year):
                self.fields['end_academic_year'].initial = current_academic_year
            else:
                self.fields['end_academic_year'].initial = partnership.end_academic_year
            if is_adri or partnership_type != PartnershipType.MOBILITY.name:
                self.fields['start_academic_year'].initial = partnership.start_academic_year
            else:
                del self.fields['start_academic_year']
            self.fields['from_academic_year'].initial = current_academic_year
        else:
            # Create
            self.fields['start_academic_year'].initial = current_academic_year
            del self.fields['from_academic_year']
            self.fields['end_academic_year'].initial = current_academic_year

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


class PartnershipYearGeneralForm(PartnershipYearSubtypeMixin, PartnershipYearBaseForm):
    class Meta(PartnershipYearBaseForm.Meta):
        fields = PartnershipYearBaseForm.Meta.fields + (
            'subtype',
            'description',
        )
        widgets = {
            **PartnershipYearBaseForm.Meta.widgets,
            'subtype': forms.RadioSelect
        }

    def __init__(self, partnership_type=None, *args, **kwargs):
        super().__init__(partnership_type, *args, **kwargs)
        self.fields['subtype'].label = _('partnership_subtype_agreement')


class PartnershipYearMobilityForm(PartnershipYearWithoutDatesForm):
    class Meta(PartnershipYearBaseForm.Meta):
        fields = PartnershipYearBaseForm.Meta.fields + (
            'is_sms',
            'is_smp',
            'is_smst',
            'is_sta',
            'is_stt',
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
                if 'start_academic_year' in self.fields:
                    self.fields['start_academic_year'].queryset = future_academic_years
                if 'from_academic_year' in self.fields:
                    self.fields['from_academic_year'].queryset = future_academic_years
                self.fields['end_academic_year'].queryset = future_academic_years

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


class PartnershipYearCourseForm(PartnershipYearSubtypeMixin, PartnershipYearWithoutDatesForm):
    class Meta(PartnershipYearWithoutDatesForm.Meta):
        fields = PartnershipYearWithoutDatesForm.Meta.fields + (
            'subtype',
            'description',
        )
        widgets = {
            **PartnershipYearWithoutDatesForm.Meta.widgets,
            'subtype': forms.RadioSelect
        }

    def __init__(self, partnership_type=None, *args, **kwargs):
        super().__init__(partnership_type, *args, **kwargs)
        self.fields['subtype'].label = _('partnership_subtype_course')


class PartnershipYearDoctorateForm(PartnershipYearSubtypeMixin, PartnershipYearBaseForm):
    class Meta(PartnershipYearBaseForm.Meta):
        fields = PartnershipYearBaseForm.Meta.fields + (
            'subtype',
            'description',
        )
        widgets = {
            **PartnershipYearBaseForm.Meta.widgets,
            'subtype': forms.RadioSelect
        }

    def __init__(self, partnership_type=None, *args, **kwargs):
        super().__init__(partnership_type, *args, **kwargs)
        self.fields['subtype'].label = _('partnership_subtype_doctorate')

        fixed_level = PartnershipYearEducationLevel.objects.filter(
            education_group_types__name=TrainingType.PHD.name,
        ).first()
        self.fields['education_levels'].initial = [fixed_level.pk]
        self.fields['education_levels'].disabled = True

        self.fields['entities'].label = _("partnership_doctorate_years_entity")
        self.fields['entities'].queryset = Entity.objects.filter(
            entityversion__entity_type=DOCTORAL_COMMISSION,
        )
        self.fields['entities'].widget.forward += [
            Const(PartnershipType.DOCTORATE.name, 'partnership_type')
        ]


class PartnershipYearProjectForm(PartnershipYearBaseForm):
    class Meta(PartnershipYearBaseForm.Meta):
        fields = PartnershipYearBaseForm.Meta.fields + (
            'funding_type',
            'description',
            'id_number',
            'project_title',
            'ucl_status',
        )
        widgets = {
            **PartnershipYearBaseForm.Meta.widgets,
            'funding_type': autocomplete.ModelSelect2(),
        }
