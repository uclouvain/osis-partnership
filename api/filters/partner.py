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

    class Meta:
        model = Partner
        fields = ['ordering']
