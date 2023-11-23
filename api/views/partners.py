from collections import defaultdict

from django.utils.dateparse import parse_date
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.permissions import AllowAny

from partnership.models import (
    Partner,
    PartnershipPartnerRelation,
    PartnershipConfiguration,
)
from rest_framework.response import Response

from ..filters import PartnerFilter, PartnershipPartnerRelationFilter
from ..serializers import PartnerListSerializer
from ..serializers.partner import InternshipPartnerSerializer, DeclareOrganizationAsInternshipPartnerSerializer


class PartnersApiListView(generics.ListAPIView):
    serializer_class = PartnerListSerializer
    permission_classes = (AllowAny,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = PartnerFilter
    pagination_class = None
    counts = None
    address_fields_to_annotate = (
        'country__continent__name',
        'country__iso_code',
        'country__name',
        'city',
        'location',
    )

    def get_partnerships_query(self, academic_year):
        # Partnership relations queryset for count
        qs = PartnershipPartnerRelation.objects.annotate_partner_address(
            *self.address_fields_to_annotate
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
            Partner.objects.annotate_address(*self.address_fields_to_annotate)
            .filter(pk__in=self.counts.keys())
            .distinct()
            .order_by('pk')
            .only(
                'uuid',
                'organization__name',
            )
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['counts'] = self.counts
        return context


class InternshipPartnerListApiView(generics.CreateAPIView, generics.ListAPIView):
    """
    Internship are partner with different constraints than usual.
    """

    serializer_class = InternshipPartnerSerializer

    def get_queryset(self):
        return Partner.objects.prefetch_address().filter(changed__gte=self.from_date)

    def list(self, request, *args, **kwargs):
        if 'from_date' not in request.query_params:
            return Response(data={'error': 'Missing from_date param.'}, status=status.HTTP_400_BAD_REQUEST)
        self.from_date = parse_date(request.query_params['from_date'])
        if self.from_date is None:
            return Response(data={'error': 'Incorrect from_date format.'}, status=status.HTTP_400_BAD_REQUEST)
        return super().list(request, *args, **kwargs)


class DeclareOrganizationAsInternshipPartnerApiView(generics.CreateAPIView):
    """
    Declare an existing organization as an internship partner
    """

    serializer_class = DeclareOrganizationAsInternshipPartnerSerializer


class InternshipPartnerDetailApiView(generics.RetrieveAPIView):
    """
    Internship are partner with different constraints than usual.
    """

    serializer_class = InternshipPartnerSerializer
    lookup_field = 'uuid'

    def get_queryset(self):
        return Partner.objects.prefetch_address()
