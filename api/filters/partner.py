from django_filters import rest_framework as filters

from partnership.models import Partner

__all__ = [
    'PartnerFilter',
]


class PartnerFilter(filters.FilterSet):
    ordering = filters.OrderingFilter(
        fields=(
            ('organization__name', 'partner'),
            ('country_iso_code', 'country_en'),
            ('city', 'city'),
        )
    )
    name = filters.CharFilter(
        field_name='organization__name',
        lookup_expr='icontains',
    )

    class Meta:
        model = Partner
        fields = ['ordering', 'name']
