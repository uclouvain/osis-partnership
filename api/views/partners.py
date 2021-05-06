from collections import defaultdict

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.permissions import AllowAny

from partnership.models import (
    Partner,
    PartnershipPartnerRelation,
    PartnershipConfiguration,
)
from ..filters import PartnerFilter, PartnershipPartnerRelationFilter
from ..serializers import PartnerListSerializer


class PartnersApiListView(generics.ListAPIView):
    serializer_class = PartnerListSerializer
    permission_classes = (AllowAny,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = PartnerFilter
    pagination_class = None
    counts = None

    def get_partnerships_query(self, academic_year):
        # Partnership relations queryset for count
        qs = PartnershipPartnerRelation.objects.annotate_partner_address(
            'country__continent__name',
            'country__iso_code',
            'city',
        ).filter_for_api(academic_year)
        partnerships_filter = PartnershipPartnerRelationFilter(
            data=self.request.query_params,
            queryset=qs,
            request=self.request,
        )
        partnerships_filter.is_valid()
        return partnerships_filter.qs.distinct('pk').order_by('pk')

    def get_queryset(self):
        academic_year = PartnershipConfiguration.get_configuration().get_current_academic_year_for_api()
        qs = self.get_partnerships_query(academic_year)

        # Because the partnership query is much faster than a linked subquery,
        # We query the partner id with the normal filters, do a count and pass
        # the count to the serializer, returning filtered partners on pk
        self.counts = defaultdict(int)
        for result in qs.values('entity__organization__partner'):
            self.counts[result['entity__organization__partner']] += 1

        return (
            Partner.objects
            .annotate_address(
                'country__continent__name',
                'country__iso_code',
                'country__name',
                'city',
                'location',
            )
            .filter(pk__in=self.counts.keys())
            .distinct().order_by('pk').only(
                'uuid',
                'organization__name',
            )
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['counts'] = self.counts
        return context
