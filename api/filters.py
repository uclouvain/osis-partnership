from django import forms
from django.db.models.expressions import Exists, OuterRef
from django.db.models.query_utils import Q
from django.utils.translation import ugettext_lazy as _
from django_filters import rest_framework as filters

from partnership.models import Partner, UCLManagementEntity


class SupervisorFilter(filters.Filter):
    field_class = forms.UUIDField

    def filter(self, qs, value):
        return (
            qs.annotate(
                has_supervisor_with_entity=Exists(UCLManagementEntity.objects
                    .filter(
                        entity__isnull=False,
                        entity=OuterRef('partnerships__ucl_university_labo'),
                        faculty=OuterRef('partnerships__ucl_university'),
                        academic_responsible__uuid=value,
                    )
                ), has_supervisor_without_entity=Exists(UCLManagementEntity.objects
                    .filter(
                        entity__isnull=True,
                        faculty=OuterRef('partnerships__ucl_university'),
                        academic_responsible__uuid=value,
                    )
                ))
                .filter(Q(partnerships__supervisor__uuid=value)
                        | Q(partnerships__supervisor__isnull=True,
                            has_supervisor_with_entity=True)
                        | Q(partnerships__supervisor__isnull=True,
                            partnerships__ucl_university_labo__isnull=True,
                            has_supervisor_without_entity=True))
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
    continent = filters.CharFilter(field_name='contact_address__country__continent__name', lookup_expr='iexact')
    country = filters.CharFilter(field_name='contact_address__country__iso_code', lookup_expr='iexact')
    city = filters.CharFilter(field_name='contact_address__city', lookup_expr='iexact')
    partner = filters.UUIDFilter(field_name='uuid')
    ucl_university = filters.UUIDFilter(
        field_name='partnerships__ucl_university__uuid',
        distinct=True,
    )
    ucl_university_labo = filters.UUIDFilter(
        field_name='partnerships__ucl_university_labo__uuid',
        distinct=True,
    )

    # Must be moved to a specific filter class because FilterSet are too limited
    supervisor = SupervisorFilter(label=_('partnership_supervisor'))

    # Depends on the current year
    # education_field
    # mobility_type
    # funding


    class Meta:
        model = Partner
        fields = [
            'ordering',
            'continent', 'country', 'city', 'partner',
            'ucl_university', 'ucl_university_labo',
            'supervisor',
        ]
