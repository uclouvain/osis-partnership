from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Func, OuterRef, Q
from django.forms import modelformset_factory
from django.utils.translation import gettext_lazy as _

from base.forms.utils.datefield import DATE_FORMAT, DatePickerInput
from base.models.entity_version import EntityVersion
from base.models.person import Person
from base.utils.cte import CTESubquery
from partnership.auth.predicates import is_linked_to_adri_entity
from partnership.auth.roles.partnership_manager import PartnershipEntityManager
from partnership.models import Partnership, EntityProxy, PartnershipDiplomaWithUCL, PartnershipProductionSupplement, \
    PartnershipPartnerRelation
from partnership.utils import format_partner_entity
from ..fields import EntityChoiceField, PersonChoiceField

__all__ = [
    'PartnershipGeneralForm',
    'PartnershipMobilityForm',
    'PartnershipCourseForm',
    'PartnershipDoctorateForm',
    'PartnershipProjectForm',
]

class PartnershipBaseForm(forms.ModelForm):
    partner_entities = forms.ModelMultipleChoiceField(
        label=_('partner'),
        queryset=EntityProxy.objects.partner_entities(),
        widget=autocomplete.ModelSelect2Multiple(
            url='partnerships:autocomplete:partner_entity'
        ),
    )

    ucl_entity = EntityChoiceField(
        label=_('ucl_entity'),
        # This is actually refined in form and autocomplete
        queryset=EntityProxy.objects.all(),
        widget=autocomplete.ModelSelect2(
            url='partnerships:autocomplete:ucl_entity',
            attrs={
                'class': 'resetting',
                'data-reset': '#id_ucl_university_labo',
            },
            forward=['partnership_type'],
        ),
    )

    supervisor = PersonChoiceField(
        label=_('partnership_supervisor'),
        queryset=Person.objects.all(),
        widget=autocomplete.ModelSelect2(
            url='partnerships:autocomplete:person',
        ),
    )

    class Meta:
        model = Partnership
        fields = (
            'partnership_type',
            'partner_entities',
            'ucl_entity',
            'supervisor',
            'comment',
            'tags',
            'is_public',
            'missions',
        )
        widgets = {
            'tags': autocomplete.Select2Multiple(),
            'partnership_type': forms.HiddenInput(),
            'missions': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, partnership_type=None, *args, **kwargs):
        """
        :type partnership_type: str
        """
        self.user = kwargs.pop('user', None)
        self.partnership_type = partnership_type

        # Initialise partnership_type for creation
        kwargs['initial']['partnership_type'] = partnership_type

        # TODO only allow sub-entities to be choosed on editing for faculty manager

        super().__init__(*args, **kwargs)

        self.fields['comment'].widget.attrs['rows'] = 3
        self.fields['partner_entities'].label_from_instance = format_partner_entity

        # Prevent type modification for updating
        if self.instance.pk:
            self.fields['partnership_type'].disabled = True

        if 'subtype' in self.fields:
            field_subtype = self.fields['subtype']

            # Constraint according to partnership type
            condition = Q(
                types__contains=[self.partnership_type],
                is_active=True
            )

            # Allow inactive types already set only for update
            if self.instance.pk:
                condition |= Q(pk=self.instance.subtype_id)
            field_subtype.queryset = field_subtype.queryset.filter(condition)

            # Prevent empty value from showing
            field_subtype.empty_label = None

        if 'description' in self.fields:
            self.fields['description'].widget.attrs['rows'] = 3

        # Fill the missions field according to the current type
        field_missions = self.fields['missions']
        field_missions.label_from_instance = lambda o: o.label
        field_missions.queryset = field_missions.queryset.filter(
            types__contains=[self.partnership_type],
        ).order_by('label')
        # If only one mission available, force it
        if len(field_missions.queryset) == 1:
            field_missions.initial = field_missions.queryset
            field_missions.widget = forms.MultipleHiddenInput()
            field_missions.disabled = True

    def clean(self):
        data = super().clean()

        # Make project acronym required if multiple partner entities
        if 'project_acronym' in data and len(data['partner_entities']) > 1 and not data['project_acronym']:
            self.add_error('project_acronym', ValidationError(_('required')))

        return data

    def clean_partner_entities(self):
        partner_entities = self.cleaned_data['partner_entities']

        # When updating, check if we changed the partner_entities
        if self.instance.pk and set(partner_entities) == set(self.instance.partner_entities.all()):
            return partner_entities

        # If changed, check that we did not set an inactive entity
        for entity in partner_entities:
            if not entity.organization.partner.is_actif:
                raise ValidationError(_('partnership_inactif_partner_error'))
        return partner_entities


class PartnershipWithDatesMixin(PartnershipBaseForm):
    class Meta(PartnershipBaseForm.Meta):
        fields = PartnershipBaseForm.Meta.fields + (
            'start_date',
            'end_date',
        )
        widgets = {
            **PartnershipBaseForm.Meta.widgets,
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


class PartnershipGeneralForm(PartnershipWithDatesMixin):
    class Meta(PartnershipWithDatesMixin.Meta):
        fields = PartnershipWithDatesMixin.Meta.fields + (
            'subtype',
            'description',
            'project_acronym',
        )
        widgets = {
            **PartnershipWithDatesMixin.Meta.widgets,
            'subtype': forms.RadioSelect,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subtype'].label = _('partnership_subtype_agreement')
        self.fields['subtype'].label_from_instance = lambda o: o.label


class PartnershipMobilityForm(PartnershipBaseForm):
    def __init__(self, partnership_type=None, *args, **kwargs):
        super().__init__(partnership_type, *args, **kwargs)
        self.fields['partner_entities'].widget.attrs = {
            'data-maximum-selection-length': 1,
        }

        field = self.fields['ucl_entity']
        field.queryset = field.queryset.filter(
            self.get_partnership_entities_managed(self.user)
        ).distinct()

        if not is_linked_to_adri_entity(self.user):
            # Restrict fields for GF and GS
            if field.queryset.count() == 1:
                field.initial = field.queryset.first().pk
                field.disabled = True

            if self.instance.pk is not None:
                # TODO This is a guess, need to check with Bart
                self.fields['partner_entities'].disabled = True

            del self.fields['is_public']

        self.fields['supervisor'].required = False
        self.fields['supervisor'].widget.attrs = {
            'data-placeholder': _('same_supervisor_than_management_entity')
        }

    @classmethod
    def get_partnership_entities_managed(cls, user):
        """
        Filter entities :
            - must have UCLManagementEntity associated
            - if user is not adri, only entities the user is allowed to manage

        :param user:
        :return: Q object
        """
        # Must have UCL management entity
        conditions = Q(uclmanagement_entity__isnull=False)

        if not is_linked_to_adri_entity(user):
            # Get children entities which user has a PartnershipEntityManager
            cte = EntityVersion.objects.with_children(entity_id=OuterRef('pk'))
            qs = cte.join(
                PartnershipEntityManager, entity_id=cte.col.entity_id
            ).with_cte(cte).filter(person=user.person).annotate(
                child_entity_id=Func(cte.col.children, function='unnest'),
            )

            # Restrict fields for GF and GS
            conditions &= Q(
                pk__in=CTESubquery(qs.values('child_entity_id'))
            )
        return conditions

    def clean_partner_entities(self):
        # For mobility type, there's no multilateral partnerships
        if len(self.cleaned_data['partner_entities']) > 1:
            raise ValidationError(_('no_multilateral_for_mobility'))
        return super().clean_partner_entities()


class PartnershipCourseForm(PartnershipBaseForm):
    ucl_reference =  forms.ChoiceField(
        label=_('ucl_reference'),
        choices=[('True', 'Oui'), ('False', 'Non')],)

    partner_referent = forms.ModelChoiceField(
        label=_('partner_referent'),
        required=False,
        queryset=EntityProxy.objects.partner_entities(),
        widget=autocomplete.ModelSelect2(
            url='partnerships:autocomplete:reference_partner_entity',
            forward=['partner_entities', 'ucl_reference'],
            attrs = {"disabled": "disabled" }
        ),
    )

    all_student = forms.ChoiceField(
        label=_('all_student'),
        choices=[('True', 'Oui'), ('False', 'Non')],
    )

    diploma_prod_by_ucl = forms.ChoiceField(
        label=_('diploma_prod_by_ucl'),
        choices=[('True', 'Oui'), ('False', 'Non')],
    )

    diploma_by_ucl = forms.ChoiceField(
        label=_('diploma_by_ucl'),
        choices=PartnershipDiplomaWithUCL.choices,
    )

    supplement_prod_by_ucl = forms.ChoiceField(
        label=_('supplement_prod_by_ucl'),
        choices=PartnershipProductionSupplement.choices(),
    )

    class Meta(PartnershipBaseForm.Meta):
        fields = PartnershipBaseForm.Meta.fields + (
            'subtype',
            'description',
            'project_acronym',
            'ucl_reference',
            'partner_referent',
            'all_student',
            'diploma_prod_by_ucl',
            'diploma_by_ucl',
            'supplement_prod_by_ucl'
        )
        widgets = {
            **PartnershipBaseForm.Meta.widgets,
            'subtype': forms.RadioSelect,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subtype'].label = _('partnership_subtype_course')
        self.fields['subtype'].label_from_instance = lambda o: o.label
        self.fields['supervisor'].required = False


class PartnershipDoctorateForm(PartnershipBaseForm):
    class Meta(PartnershipBaseForm.Meta):
        fields = PartnershipBaseForm.Meta.fields + (
            'subtype',
            'description',
            'project_acronym',
        )
        widgets = {
            **PartnershipBaseForm.Meta.widgets,
            'subtype': forms.RadioSelect,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subtype'].label = _('partnership_subtype_doctorate')
        self.fields['subtype'].label_from_instance = lambda o: o.label

class PartnershipProjectForm(PartnershipWithDatesMixin):
    class Meta(PartnershipWithDatesMixin.Meta):
        fields = PartnershipWithDatesMixin.Meta.fields + (
            'description',
            'id_number',
            'project_acronym',
            'project_title',
            'ucl_status',
        )



class PartnershipPartnerRelationForm(forms.ModelForm):
    partners = forms.ModelChoiceField(
        label=_('Partner entités'),
        required=True,
        queryset=EntityProxy.objects.partner_entities(),
        widget=autocomplete.ModelSelect2(
            url='partnerships:autocomplete:complement',
            forward=['partnership'],
        ),
    )

    class Meta:
        model = PartnershipPartnerRelation
        fields = [
            # 'entity',
            'partners',
            'diploma_with_ucl_by_partner',
            'diploma_prod_by_partner',
            'supplement_prod_by_partner',
            'partnership'
        ]

        widgets = {
            # 'entity': forms.Select,
            'partnership': forms.HiddenInput,
        }


PartnershipPartnerRelationFormSet = modelformset_factory(
    PartnershipPartnerRelation,
    form=PartnershipPartnerRelationForm,
    extra=0
)