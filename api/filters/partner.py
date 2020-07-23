from django import forms
from django.db.models import Exists, OuterRef, Q
from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as filters

from partnership.models import Financing, Partner, UCLManagementEntity
from .mixins import FundingFilterMixin

__all__ = [
    'PartnerSupervisorFilter',
    'PartnerEducationFieldFilter',
    'PartnerFundingFilter',
    'PartnerMobilityTypeFilter',
    'PartnerFilter',
]


class PartnerSupervisorFilter(filters.Filter):
    field_class = forms.UUIDField

    def filter(self, qs, value):
        if not value:
            return qs
        return (
            qs.annotate(
                has_supervisor_with_entity=Exists(
                    UCLManagementEntity.objects.filter(
                        entity=OuterRef('partnerships__ucl_entity'),
                        academic_responsible__uuid=value,
                    )
                ),
            ).filter(
                Q(partnerships__supervisor__uuid=value)
                | Q(partnerships__supervisor__isnull=True,
                    has_supervisor_with_entity=True)
            )
        )


class PartnerEducationFieldFilter(filters.Filter):
    field_class = forms.UUIDField

    def filter(self, qs, value):
        if not value:
            return qs
        return qs.filter(partnerships__years__education_fields__uuid=value)


class PartnerMobilityTypeFilter(filters.Filter):
    field_class = forms.MultipleChoiceField

    def __init__(self, **kwargs):
        choices = (('student', "Student"), ('staff', "Staff"))
        super().__init__(choices=choices, **kwargs)

    def filter(self, qs, value):
        if not value:
            return qs
        filter_qs = Q()
        if 'student' in value:
            filter_qs = (
                Q(partnerships__years__is_sms=True)
                | Q(partnerships__years__is_smst=True)
                | Q(partnerships__years__is_smp=True)
            )
        if 'staff' in value:
            filter_qs = (
                Q(partnerships__years__is_stt=True)
                | Q(partnerships__years__is_sta=True)
            )
        return qs.filter(filter_qs)


class PartnerFundingFilter(FundingFilterMixin, filters.ModelMultipleChoiceFilter):
    def filter(self, qs, value):
        if not value:
            return qs
        filter_qs = Q()
        for funding in value:
            filter_qs |= Q(type_id=funding.pk)
        return (
            qs
            .annotate_address('country_id')
            .annotate(
                has_funding=Exists(
                    Financing.objects
                    .filter(
                        filter_qs,
                        countries=OuterRef('country_id'),
                        academic_year=OuterRef('current_academic_year'),
                    )
                )
            ).filter(has_funding=True)
        )


class PartnerFilter(filters.FilterSet):
    ordering = filters.OrderingFilter(
        fields=(
            ('organization__name', 'partner'),
            ('country_iso_code', 'country_en'),
            ('city', 'city'),
            ('partnerships__ucl_entity', 'ucl_entity'),
            ('subject_area_ordered', 'subject_area'),
        )
    )
    continent = filters.CharFilter(
        field_name='country_continent_name',
        lookup_expr='iexact',
    )
    country = filters.CharFilter(
        field_name='country_iso_code',
        lookup_expr='iexact',
    )
    city = filters.CharFilter(field_name='city', lookup_expr='iexact')
    partner = filters.UUIDFilter(field_name='uuid')
    ucl_entity = filters.UUIDFilter(
        field_name='partnerships__ucl_entity__uuid',
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
            'ucl_entity',
            'supervisor', 'education_field', 'mobility_type',
        ]
