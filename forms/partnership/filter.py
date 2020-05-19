from dal import autocomplete
from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear
from base.models.entity import Entity
from base.models.person import Person
from partnership.models import (
    Address, Partner, PartnerEntity, PartnerTag, PartnerType, PartnershipTag,
    PartnershipYear,
    PartnershipYearEducationLevel,
    PartnershipType,
)
from reference.models.continent import Continent
from reference.models.country import Country
from reference.models.domain_isced import DomainIsced
from ..fields import EntityChoiceField
from ..widgets import CustomNullBooleanSelect

__all__ = ['PartnershipFilterForm']


class PartnershipFilterForm(forms.Form):
    # UCL

    ucl_entity = EntityChoiceField(
        label=_('faculty_entity_filter'),
        queryset=Entity.objects.filter(partnerships__isnull=False).distinct(),
        empty_label=_('ucl_entity'),
        required=False,
        widget=autocomplete.ModelSelect2(
            url='partnerships:autocomplete:ucl_entity_filter',
            attrs={
                'data-width': '100%',
                'data-reset': '#id_years_entity,#id_university_offer',
            },
        ),
    )
    ucl_entity_with_child = forms.BooleanField(
        label=_('Include subordinate entities'),
        required=False,
    )

    education_level = forms.ModelChoiceField(
        label=_('education_level_filter'),
        queryset=PartnershipYearEducationLevel.objects.filter(partnerships_years__isnull=False).distinct(),
        widget=autocomplete.ModelSelect2(
            attrs={
                'data-width': '100%',
                'class': 'resetting',
                'data-reset': '#id_university_offer',
            }
        ),
        required=False,
    )

    years_entity = forms.ModelChoiceField(
        label=_('entity_filter'),
        queryset=Entity.objects.filter(partnerships_years__isnull=False).distinct(),
        required=False,
        widget=autocomplete.ModelSelect2(
            url='partnerships:autocomplete:years_entity_filter',
            forward=['ucl_entity'],
            attrs={
                'data-width': '100%',
                'class': 'resetting',
                'data-reset': '#id_university_offer',
            },
        ),
    )

    university_offer = forms.ModelChoiceField(
        label=_('university_offers_filter'),
        queryset=(
            EducationGroupYear.objects
                .select_related('academic_year')
                .filter(partnerships__isnull=False)
                .distinct()
        ),
        required=False,
        widget=autocomplete.ModelSelect2(
            url='partnerships:autocomplete:university_offers_filter',
            forward=['ucl_entity', 'education_level', 'years_entity'],
            attrs={'data-width': '100%'},
        ),
    )

    # Partner

    partner = forms.ModelChoiceField(
        label=_('partner'),
        queryset=Partner.objects.filter(partnerships__isnull=False).distinct(),
        empty_label=_('partner'),
        widget=autocomplete.ModelSelect2(
            attrs={
                'data-width': '100%',
                'class': 'resetting',
                'data-reset': '#id_partner_entity',
            },
            url='partnerships:autocomplete:partner_partnerships_filter',
        ),
        required=False,
    )
    partner_entity = forms.ModelChoiceField(
        label=_('partner_entity'),
        queryset=PartnerEntity.objects.filter(partnerships__isnull=False).distinct(),
        empty_label=_('partner_entity'),
        widget=autocomplete.ModelSelect2(
            attrs={'data-width': '100%'},
            url='partnerships:autocomplete:partner_entity_partnerships_filter',
            forward=['partner'],
        ),
        required=False,
    )
    partner_type = forms.ModelChoiceField(
        label=_('partner_type'),
        queryset=PartnerType.objects.filter(partners__partnerships__isnull=False).distinct(),
        empty_label=_('partner_type'),
        required=False,
    )
    erasmus_code = forms.CharField(
        label=_('erasmus_code'),
        widget=forms.TextInput(attrs={'placeholder': _('erasmus_code')}),
        required=False,
    )
    use_egracons = forms.NullBooleanField(
        label=_('use_egracons'),
        widget=CustomNullBooleanSelect(),
        required=False,
    )
    city = forms.ChoiceField(
        label=_('city'),
        choices=((None, _('city')),),
        widget=autocomplete.Select2(attrs={'data-width': '100%'}),
        required=False,
    )
    country = forms.ModelChoiceField(
        label=_('country'),

        queryset=(
            Country.objects
            .filter(address__partners__partnerships__isnull=False)
            .order_by('name')
            .distinct()
        ),
        empty_label=_('country'),
        widget=autocomplete.ModelSelect2(attrs={'data-width': '100%'}),
        required=False,
    )
    continent = forms.ModelChoiceField(
        label=_('continent'),
        queryset=(
            Continent.objects
            .filter(country__address__partners__partnerships__isnull=False)
            .order_by('name')
            .distinct()
        ),
        empty_label=_('continent'),
        required=False,
    )
    partner_tags = forms.ModelMultipleChoiceField(
        label=_('partner_tags'),
        queryset=PartnerTag.objects.filter(partners__partnerships__isnull=False).distinct(),
        widget=autocomplete.ModelSelect2Multiple(attrs={'data-width': '100%'}),
        required=False,
    )

    # Partnerships

    education_field = forms.ModelChoiceField(
        label=_('education_field'),
        queryset=DomainIsced.objects.filter(partnershipyear__isnull=False).distinct(),
        widget=autocomplete.ModelSelect2(attrs={'data-width': '100%'}),
        required=False,
    )
    is_sms = forms.NullBooleanField(
        label=_('is_sms'),
        widget=CustomNullBooleanSelect(),
        required=False,
    )
    is_smp = forms.NullBooleanField(
        label=_('is_smp'),
        widget=CustomNullBooleanSelect(),
        required=False,
    )
    is_sta = forms.NullBooleanField(
        label=_('is_sta'),
        widget=CustomNullBooleanSelect(),
        required=False,
    )
    is_stt = forms.NullBooleanField(
        label=_('is_stt'),
        widget=CustomNullBooleanSelect(),
        required=False,
    )
    partnership_type = forms.ChoiceField(
        label=_('partnership_type'),
        choices=((None, '---------'),) + PartnershipType.choices(),
        required=False,
    )
    supervisor = forms.ModelChoiceField(
        label=_('partnership_supervisor'),
        queryset=Person.objects
            .filter(Q(partnerships_supervisor__isnull=False) | Q(management_entities__isnull=False))
            .order_by('last_name')
            .distinct(),
        widget=autocomplete.ModelSelect2(attrs={'data-width': '100%'}),
        required=False,
    )
    tags = forms.ModelMultipleChoiceField(
        label=_('tags'),
        queryset=PartnershipTag.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(attrs={'data-width': '100%'}),
        required=False,
    )

    partnership_in = forms.ModelChoiceField(
        label=_('partnership_in'),
        help_text=_('parnership_in_help_text'),
        queryset=AcademicYear.objects.all(),
        required=False,
    )
    partnership_ending_in = forms.ModelChoiceField(
        label=_('partnership_ending_in'),
        help_text=_('parnership_ending_in_help_text'),
        queryset=AcademicYear.objects.all(),
        required=False,
    )
    partnership_valid_in = forms.ModelChoiceField(
        label=_('partnership_valid_in'),
        queryset=AcademicYear.objects.all(),
        required=False,
    )
    partnership_not_valid_in = forms.ModelChoiceField(
        label=_('partnership_not_valid_in'),
        queryset=AcademicYear.objects.all(),
        required=False,
    )
    partnership_with_no_agreements_in = forms.ModelChoiceField(
        label=_('partnership_with_no_agreements_in'),
        help_text=_('partnership_with_no_agreements_in_help_text'),
        queryset=AcademicYear.objects.all(),
        required=False,
    )
    comment = forms.CharField(
        label=_('comment'),
        required=False,
    )
    ordering = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cities
        cities = (
            Address.objects
            .filter(partners__partnerships__isnull=False, city__isnull=False)
            .values_list('city', flat=True)
            .order_by('city')
            .distinct('city')
        )
        self.fields['city'].choices = ((None, _('city')),) + tuple((city, city) for city in cities)
        # Partnership types
        partnership_types = (
            PartnershipYear.objects
                .values_list('partnership_type', flat=True)
                .order_by('partnership_type')
                .distinct('partnership_type')
        )
        types_dict = dict(PartnershipType.choices())
        choices = sorted([
            (partnership_type, types_dict.get(partnership_type, partnership_type))
            for partnership_type in partnership_types
        ], key=lambda x: x[1])
        self.fields['partnership_type'].choices = ((None, _('partnership_type')),) + tuple(choices)

    def clean_ordering(self):
        # Django filters expects a list
        ordering = self.cleaned_data.get('ordering')
        if ordering:
            return [ordering]
