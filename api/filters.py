from django_filters import rest_framework as filters

from partnership.models import Partner


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
    supervisor = filters.UUIDFilter(
        field_name='partnerships__supervisor__uuid', # | 'management_entity__academic_responsible'
        distinct=True,
    )
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
        ]
