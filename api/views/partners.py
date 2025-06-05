from collections import defaultdict

from django.utils.dateparse import parse_date
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.contrib.django_filters import DjangoFilterExtension
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import AllowAny

from osis_role.contrib.views import APIPermissionRequiredMixin
from partnership.models import (
    Partner,
    PartnershipPartnerRelation,
    PartnershipConfiguration,
)
from rest_framework.response import Response

from ..filters import PartnershipPartnerRelationFilter, PartnerFilter
from ..serializers import PartnerListSerializer
from ..serializers.partner import InternshipPartnerSerializer, DeclareOrganizationAsInternshipPartnerSerializer


@extend_schema_view(
    get=extend_schema(
        parameters=[
            # Parameters from PartnershipPartnerRelationFilter
            OpenApiParameter(
                'continent',
                OpenApiTypes.STR,
                description='The continent name',
            ),
            OpenApiParameter(
                'country',
                OpenApiTypes.STR,
                description='The country iso code',
            ),
            OpenApiParameter(
                'city',
                OpenApiTypes.STR,
                description='The city name',
            ),
            OpenApiParameter(
                'partner',
                OpenApiTypes.UUID,
                description='The uuid of the partner',
            ),
            OpenApiParameter(
                'ucl_entity',
                OpenApiTypes.UUID,
                description='The uuid of the faculty or school',
            ),
            OpenApiParameter(
                'with_children',
                OpenApiTypes.BOOL,
                description='If children of ucl_entity should be taken into account',
            ),
            OpenApiParameter(
                'type',
                OpenApiTypes.STR,
                description='The type of partnership',
                enum=[
                    'GENERAL',
                    'MOBILITY',
                    'COURSE',
                    'DOCTORATE',
                    'PROJECT',
                ],
            ),
            OpenApiParameter(
                'education_level',
                OpenApiTypes.STR,
                description='The education level code',
            ),
            OpenApiParameter(
                'tag',
                OpenApiTypes.STR,
                description='The tag of the partnership',
            ),
            OpenApiParameter(
                'partner_tag',
                OpenApiTypes.STR,
                description='The tag of the partner',
            ),
            OpenApiParameter(
                'education_field',
                OpenApiTypes.UUID,
                description='The uuid of the education field',
            ),
            OpenApiParameter(
                'offer',
                OpenApiTypes.UUID,
                description='The uuid of the offer',
            ),
            OpenApiParameter(
                'mobility_type',
                OpenApiTypes.STR,
                description='The type of mobility, either for student or for staff',
                enum=['student', 'staff',]
            ),
            OpenApiParameter(
                'flow_direction',
                OpenApiTypes.NUMBER,
                description='The source id of funding',
            ),
            OpenApiParameter(
                'funding_source',
                OpenApiTypes.NUMBER,
                description='The source id of funding',
            ),
            OpenApiParameter(
                'funding_program',
                OpenApiTypes.NUMBER,
                description='The program id of funding',
            ),
            OpenApiParameter(
                'funding_type',
                OpenApiTypes.NUMBER,
                description='The type id of funding',
            ),
            OpenApiParameter(
                'bbox',
                OpenApiTypes.STR,
                description='The bounding box to export the partnerships',
                examples=[OpenApiExample('bbox', '5.2,10.5,5.7,10.9')],
            ),
        ],
    ),
)
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


@extend_schema_view(
    get=extend_schema(
        parameters=[OpenApiParameter(
            name='from_date',
            type=OpenApiTypes.DATE,
            description='A date in the ISO format',
            required=True,
            examples=[OpenApiExample('date', '2023-10-12')],
        )],
    )
)
class InternshipPartnerListApiView(generics.CreateAPIView, generics.ListAPIView):
    """
    Internship are partner with different constraints than usual.
    """

    serializer_class = InternshipPartnerSerializer

    def get_queryset(self):
        if not hasattr(self, 'from_date'):
            # Used for schema generation
            return Partner.objects.none()
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


class InternshipPartnerDetailApiView(APIPermissionRequiredMixin, generics.RetrieveAPIView):
    """
    Internship are partner with different constraints than usual.
    """

    serializer_class = InternshipPartnerSerializer
    lookup_field = 'uuid'

    # APIPermissionRequiredMixin
    permission_mapping = {
        'GET': 'partnership.can_access_partners',
    }

    def get_queryset(self):
        return Partner.objects.prefetch_address()
