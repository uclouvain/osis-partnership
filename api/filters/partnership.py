from django import forms
from django.db.models import Exists, OuterRef, Q
from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as filters

from partnership.models import Financing, Partnership, UCLManagementEntity
from .mixins import FundingFilterMixin


class PartnershipSupervisorFilter(filters.Filter):
    field_class = forms.UUIDField

    def filter(self, qs, value):
        if not value:
            return qs
        return (
            qs.annotate(
                has_supervisor_with_entity=Exists(
                    UCLManagementEntity.objects.filter(
                        entity__isnull=False,
                        entity=OuterRef('ucl_university_labo'),
                        faculty=OuterRef('ucl_university'),
                        academic_responsible__uuid=value,
                    )
                ),
                has_supervisor_without_entity=Exists(
                    UCLManagementEntity.objects.filter(
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
        return qs.filter(years__education_fields__uuid=value)


class PartnershipMobilityTypeFilter(filters.Filter):
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
                Q(years__is_sms=True)
                | Q(years__is_smst=True)
                | Q(years__is_smp=True)
            )
        if 'staff' in value:
            filter_qs = (
                Q(years__is_stt=True)
                | Q(years__is_sta=True)
            )
        return qs.filter(filter_qs)


class PartnershipFundingFilter(FundingFilterMixin, filters.ModelMultipleChoiceFilter):
    def filter(self, qs, value):
        if not value:
            return qs
        filter_qs = Q()
        for funding in value:
            filter_qs |= Q(pk=funding.pk)
        return (
            qs
            .annotate(
                has_funding=Exists(
                    Financing.objects
                    .filter(
                        filter_qs,
                        countries=OuterRef('partner__contact_address__country'),
                        academic_year=OuterRef('current_academic_year'),
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
            ('ucl_university_most_recent_acronym', 'ucl_university'),
            ('ucl_university_labo_most_recent_acronym', 'ucl_university_labo'),
            ('type_ordered', 'type'),
            ('subject_area_ordered', 'subject_area'),
        )
    )
    continent = filters.CharFilter(
        field_name='partner__contact_address__country__continent__name',
        lookup_expr='iexact',
    )
    country = filters.CharFilter(
        field_name='partner__contact_address__country__iso_code',
        lookup_expr='iexact',
    )
    city = filters.CharFilter(
        field_name='partner__contact_address__city',
        lookup_expr='iexact',
    )
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
