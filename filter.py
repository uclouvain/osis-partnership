import django_filters as filters
from django.db.models import Q
from django.db.models.functions import Now

from partnership.forms import PartnerFilterForm
from partnership.models import Partner


class PartnerAdminFilter(filters.FilterSet):
    ordering = filters.OrderingFilter(
        fields=(
            ('name', 'partner'),
            ('contact_address__country__name', 'country'),
            ('erasmus_code', 'erasmus_code'),
            ('partner_type__value', 'partner_type'),
            ('contact_address__city', 'city'),
            ('is_valid', 'is_valid'),
            ('is_actif', 'is_actif'),
        )
    )
    name = filters.CharFilter(lookup_expr='icontains')
    pic_code = filters.CharFilter(lookup_expr='icontains')
    erasmus_code = filters.CharFilter(lookup_expr='icontains')
    continent = filters.CharFilter(
        field_name='contact_address__country__continent',
    )
    country = filters.CharFilter(
        field_name='contact_address__country',
    )
    city = filters.CharFilter(
        field_name='contact_address__city',
        lookup_expr='iexact',
    )
    is_actif = filters.BooleanFilter(
        method='filter_is_actif',
    )

    class Meta:
        model = Partner
        fields = [
            'ordering',
            'name',
            'partner_type',
            'pic_code',
            'erasmus_code',
            'is_ies',
            'is_valid',
            'is_actif',
            'tags',
            'continent',
            'country',
            'city',
        ]

    def get_form_class(self):
        return PartnerFilterForm

    @staticmethod
    def filter_is_actif(queryset, name, value):
        if value:
            return queryset.filter(
                (Q(start_date__isnull=True) & Q(end_date__isnull=True))
                | (Q(start_date__lte=Now()) & Q(end_date__gte=Now()))
            )
        else:
            return queryset.filter(
                Q(start_date__gt=Now()) | Q(end_date__lt=Now())
            )
