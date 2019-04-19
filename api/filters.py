from django import forms
from django.db.models.expressions import Exists, OuterRef, F
from django.db.models.query_utils import Q
from django.utils.translation import ugettext_lazy as _
from django_filters import rest_framework as filters

from partnership.models import Partner, UCLManagementEntity, Financing, Partnership


## Partners

class PartnerSupervisorFilter(filters.Filter):
    field_class = forms.UUIDField

    def filter(self, qs, value):
        if not value:
            return qs
        return (
            qs.annotate(
                has_supervisor_with_entity=Exists(UCLManagementEntity.objects
                    .filter(
                        entity__isnull=False,
                        entity=OuterRef('partnerships__ucl_university_labo'),
                        faculty=OuterRef('partnerships__ucl_university'),
                        academic_responsible__uuid=value,
                    )
                ),
                has_supervisor_without_entity=Exists(UCLManagementEntity.objects
                    .filter(
                        entity__isnull=True,
                        faculty=OuterRef('partnerships__ucl_university'),
                        academic_responsible__uuid=value,
                    )
                )
            )
            .filter(
                Q(partnerships__supervisor__uuid=value)
                | Q(partnerships__supervisor__isnull=True,
                    has_supervisor_with_entity=True)
                | Q(partnerships__supervisor__isnull=True,
                    partnerships__ucl_university_labo__isnull=True,
                    has_supervisor_without_entity=True)
            )
        )


class PartnerEducationFieldFilter(filters.Filter):
    field_class = forms.UUIDField

    def filter(self, qs, value):
        if not value:
            return qs
        return (
            qs.filter(
                partnerships__years__academic_year=F('current_academic_year'),  # From annotation
                partnerships__years__education_fields__uuid=value,
            )
        )


class PartnerMobilityTypeFilter(filters.Filter):
    field_class = forms.CharField

    def filter(self, qs, value):
        if not value:
            return qs
        if value == 'student':
            return qs.filter(
                Q(partnerships__years__is_sms=True)
                | Q(partnerships__years__is_smst=True)
                | Q(partnerships__years__is_smp=True),
                partnerships__years__academic_year=F('current_academic_year'),  # From annotation
            )
        if value == 'staff':
            return qs.filter(
                Q(partnerships__years__is_stt=True)
                | Q(partnerships__years__is_sta=True),
                partnerships__years__academic_year=F('current_academic_year'),  # From annotation
            )


class PartnerFundingFilter(filters.Filter):
    field_class = forms.CharField

    def filter(self, qs, value):
        if not value:
            return qs
        return (
            qs
            .annotate(
                has_funding=Exists(
                    Financing.objects
                    .filter(
                        countries=OuterRef('contact_address__country'),
                        academic_year=OuterRef('current_academic_year'),
                        name__iexact=value,
                    )
                )
            ).filter(has_funding=True)
        )


class PartnerFilter(filters.FilterSet):
    ordering = filters.OrderingFilter(
        fields=(
            ('name', 'partner'),
            ('contact_address__country__name', 'country_en'),
            ('contact_address__city', 'city'),
            ('partnerships__ucl_university', 'ucl_university'),
            # ('TODO', 'subject_area'),
        )
    )
    continent = filters.CharFilter(field_name='partner__contact_address__country__continent__name', lookup_expr='iexact')
    country = filters.CharFilter(field_name='partner__contact_address__country__iso_code', lookup_expr='iexact')
    city = filters.CharFilter(field_name='partner__contact_address__city', lookup_expr='iexact')
    partner = filters.UUIDFilter(field_name='partner__uuid')
    ucl_university = filters.UUIDFilter(
        field_name='ucl_university__uuid',
        distinct=True,
    )
    ucl_university_labo = filters.UUIDFilter(
        field_name='ucl_university_labo__uuid',
        distinct=True,
    )

    supervisor = PartnerSupervisorFilter(label=_('partnership_supervisor'))

    # Depends on the current year
    education_field = PartnerEducationFieldFilter(label=_('education_field'))
    mobility_type = PartnerMobilityTypeFilter(label=_('mobility_type'))
    funding = PartnerFundingFilter(label=_('funding'))


    class Meta:
        model = Partner
        fields = [
            'ordering',
            'continent', 'country', 'city', 'partner',
            'ucl_university', 'ucl_university_labo',
            'supervisor', 'education_field', 'mobility_type',
        ]


## Partnerships

class PartnershipSupervisorFilter(filters.Filter):
    field_class = forms.UUIDField

    def filter(self, qs, value):
        if not value:
            return qs
        return (
            qs.annotate(
                has_supervisor_with_entity=Exists(UCLManagementEntity.objects
                    .filter(
                        entity__isnull=False,
                        entity=OuterRef('ucl_university_labo'),
                        faculty=OuterRef('ucl_university'),
                        academic_responsible__uuid=value,
                    )
                ),
                has_supervisor_without_entity=Exists(UCLManagementEntity.objects
                    .filter(
                        entity__isnull=True,
                        faculty=OuterRef('ucl_university'),
                        academic_responsible__uuid=value,
                    )
                )
            )
            .filter(
                Q(supervisor__uuid=value)
                | Q(supervisor__isnull=True,
                    has_supervisor_with_entity=True)
                | Q(supervisor__isnull=True,
                    ucl_university_labo__isnull=True,
                    has_supervisor_without_entity=True)
            )
        )


class PartnershipEducationFieldFilter(filters.Filter):
    field_class = forms.UUIDField

    def filter(self, qs, value):
        if not value:
            return qs
        return (
            qs.filter(
                years__academic_year=F('current_academic_year'),  # From annotation
                years__education_fields__uuid=value,
            )
        )


class PartnershipMobilityTypeFilter(filters.Filter):
    field_class = forms.CharField

    def filter(self, qs, value):
        if not value:
            return qs
        if value == 'student':
            return qs.filter(
                Q(years__is_sms=True)
                | Q(years__is_smst=True)
                | Q(years__is_smp=True),
                years__academic_year=F('current_academic_year'),  # From annotation
            )
        if value == 'staff':
            return qs.filter(
                Q(years__is_stt=True)
                | Q(years__is_sta=True),
                years__academic_year=F('current_academic_year'),  # From annotation
            )


class PartnershipFundingFilter(filters.Filter):
    field_class = forms.CharField

    def filter(self, qs, value):
        if not value:
            return qs
        return (
            qs
            .annotate(
                has_funding=Exists(
                    Financing.objects
                    .filter(
                        countries=OuterRef('partner__contact_address__country'),
                        academic_year=OuterRef('current_academic_year'),
                        name__iexact=value,
                    )
                )
            ).filter(has_funding=True)
        )


class PartnershipFilter(filters.FilterSet):
    ordering = filters.OrderingFilter(
        fields=(
            ('partner__name', 'partner'),
            ('partner__contact_address__country__name', 'country_en'),
            ('partner__contact_address__city', 'city'),
            ('ucl_university', 'ucl_university'),
            # ('TODO', 'type'),
            # ('TODO', 'subject_area'),
        )
    )
    continent = filters.CharFilter(field_name='partner__contact_address__country__continent__name', lookup_expr='iexact')
    country = filters.CharFilter(field_name='partner__contact_address__country__iso_code', lookup_expr='iexact')
    city = filters.CharFilter(field_name='partner__contact_address__city', lookup_expr='iexact')
    partner = filters.UUIDFilter(field_name='partner__uuid')
    ucl_university = filters.UUIDFilter(
        field_name='ucl_university__uuid',
        distinct=True,
    )
    ucl_university_labo = filters.UUIDFilter(
        field_name='ucl_university_labo__uuid',
        distinct=True,
    )

    supervisor = PartnershipSupervisorFilter(label=_('partnership_supervisor'))

    # Depends on the current year
    education_field = PartnershipEducationFieldFilter(label=_('education_field'))
    mobility_type = PartnershipMobilityTypeFilter(label=_('mobility_type'))
    funding = PartnershipFundingFilter(label=_('funding'))


    class Meta:
        model = Partnership
        fields = [
            'ordering',
            'continent', 'country', 'city', 'partner',
            'ucl_university', 'ucl_university_labo',
            'supervisor', 'education_field', 'mobility_type',
        ]