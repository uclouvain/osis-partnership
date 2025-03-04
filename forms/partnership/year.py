from dal import autocomplete
from dal.forward import Const
from django import forms
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory
from django.utils.translation import gettext_lazy as _
from partnership.models import EntityProxy, Partnership
from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear
from base.models.entity import Entity
from base.models.enums.education_group_types import TrainingType
from base.models.enums.entity_type import DOCTORAL_COMMISSION
from partnership.auth.predicates import is_linked_to_adri_entity
from partnership.models import (
    PartnershipConfiguration,
    PartnershipType, PartnershipYear,
    PartnershipYearEducationLevel, FundingProgram, FundingType, FundingSource,
)
from .partnership import PartnershipBaseForm
from ..fields import (
    EducationGroupYearChoiceSelect, EntityChoiceMultipleField,
    FundingChoiceField,
)

__all__ = [
    'PartnershipYearGeneralForm',
    'PartnershipYearMobilityForm',
    'PartnershipYearCourseForm',
    'PartnershipYearDoctorateForm',
    'PartnershipYearProjectForm',
]

from ...models.relation_year import PartnershipPartnerRelationYear


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
            'eligible',
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
        data = super().clean()

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


class FundingMixin(forms.Form):
    funding = FundingChoiceField(label=_('funding'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            self.fields['funding'].initial = (
                    self.instance.funding_type
                    or self.instance.funding_program
                    or self.instance.funding_source
            )

    def clean_funding(self):
        # Check funding is active if changed or new instance
        funding = self.cleaned_data.get('funding')
        if (
                (not self.instance.pk or 'funding' in self.changed_data)
                and isinstance(funding, (FundingType, FundingProgram))
                and not funding.is_active
        ):
            raise forms.ValidationError(_('Funding is not active anymore'))
        return funding

    def clean(self):
        data = super().clean()

        # Reset previous values in case of empty value
        data['funding_source'] = None
        data['funding_program'] = None
        data['funding_type'] = None

        funding = data.get('funding')
        if funding:
            # Determine funding hierarchy from value
            if isinstance(funding, FundingType):
                data['funding_source'] = funding.program.source
                data['funding_program'] = funding.program
                data['funding_type'] = funding
            elif isinstance(funding, FundingProgram):
                data['funding_source'] = funding.source
                data['funding_program'] = funding
            elif isinstance(funding, FundingSource):
                data['funding_source'] = funding

        return data


class PartnershipYearMobilityForm(FundingMixin, PartnershipYearWithoutDatesForm):
    class Meta(PartnershipYearBaseForm.Meta):
        fields = PartnershipYearBaseForm.Meta.fields + (
            'is_sms',
            'is_smp',
            'is_smst',
            'is_sta',
            'is_stt',
            'funding_source',
            'funding_program',
            'funding_type',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['funding'].help_text = _('help_text_funding_type')
        self.fields['funding'].required = False
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
        data = super().clean()

        if data['is_sms'] or data['is_smp'] or data['is_smst']:
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


class PartnershipYearCourseForm(PartnershipYearWithoutDatesForm):
    class Meta(PartnershipYearBaseForm.Meta):
        fields = PartnershipYearBaseForm.Meta.fields + (
            'all_student',
            'diploma_prod_by_ucl',
            'supplement_prod_by_ucl',
            'type_diploma_by_ucl',
            'ucl_reference',
        )

    def __init__(self, partnership_type=None, *args, **kwargs):
        super().__init__(partnership_type, *args, **kwargs)

        self.fields['education_levels'].required = True
        self.fields['diploma_prod_by_ucl'].initial = True

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



class PartnershipYearDoctorateForm(PartnershipYearWithoutDatesForm):
    def __init__(self, partnership_type=None, *args, **kwargs):
        super().__init__(partnership_type, *args, **kwargs)

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


class PartnershipYearProjectForm(FundingMixin, PartnershipYearBaseForm):
    class Meta(PartnershipYearBaseForm.Meta):
        fields = PartnershipYearBaseForm.Meta.fields + (
            'funding_source',
            'funding_program',
            'funding_type',
        )


class PartnershipRelationYearBaseForm(forms.ModelForm):
    class Meta:
        model = Partnership
        fields = ('partnership_type',)

    def __init__(self, partnership_type="COURSE", *args, **kwargs):
        self.user = kwargs.pop('user')
        self.partnership_type = partnership_type
        super().__init__(*args, **kwargs)


class PartnershipRelationYearWithoutDatesForm(PartnershipRelationYearBaseForm):
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

    def __init__(self,  *args, **kwargs):
        super().__init__(*args, **kwargs)

        config = PartnershipConfiguration.get_configuration()
        current_academic_year = config.partnership_creation_update_min_year
        is_adri = True
        # is_linked_to_adri_entity(self.user)
        if self.instance:
            # Update
            partnership = self.instance
            if (current_academic_year is not None
                    and current_academic_year.year > partnership.end_academic_year.year):
                self.fields['end_academic_year'].initial = current_academic_year
            else:
                self.fields['end_academic_year'].initial = partnership.end_academic_year
            if is_adri:
                self.fields['start_academic_year'].initial = partnership.start_academic_year
            else:
                del self.fields['start_academic_year']
            self.fields['from_academic_year'].initial = current_academic_year
        else:
            # Create
            self.fields['start_academic_year'].initial = current_academic_year
            del self.fields['from_academic_year']
            self.fields['end_academic_year'].initial = current_academic_year

        self.fields['start_academic_year'].disabled = True
        self.fields['from_academic_year'].disabled = False
        self.fields['end_academic_year'].disabled = True


    def clean(self):
        data = super().clean()
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


class PartnershipRelationYearCourseForm(forms.ModelForm):
    class Meta:
        model = PartnershipPartnerRelationYear
        fields = (
            'partner_referent',
            'diploma_prod_by_partner',
            'type_diploma_by_partner',
            'supplement_prod_by_partner',
        )
        labels = {
            'partner_referent': _('partner_referent'),
            'diploma_prod_by_partner': _('diploma_prod_by_partner'),
            'type_diploma_by_partner': _('type_diploma_by_partner'),
            'supplement_prod_by_partner': _('supplement_prod_by_partner'),
        }


PartnerRelationYearFormSet = modelformset_factory(
    PartnershipPartnerRelationYear,
    form=PartnershipRelationYearCourseForm,
    extra=0,
    can_delete=False
)
