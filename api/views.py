from django.db import models
from django.db.models.aggregates import Count
from django.db.models.expressions import Subquery, OuterRef, Value
from django.db.models.functions import Concat
from django.db.models.query import Prefetch
from django.db.models.query_utils import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from base.models.academic_year import AcademicYear
from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.person import Person
from partnership.api.filters import PartnerFilter, PartnershipFilter
from partnership.api.serializers import PartnerSerializer, PartnershipSerializer, ContinentConfigurationSerializer, \
    PartnerConfigurationSerializer, UCLUniversityConfigurationSerializer, SupervisorConfigurationSerializer, \
    EducationFieldConfigurationSerializer
from partnership.models import Partner, Partnership, PartnershipYearEducationField, PartnershipYear, \
    PartnershipConfiguration, PartnershipAgreement
from reference.models.continent import Continent


class ConfigurationView(APIView):

    permission_classes = (AllowAny,)

    def get(self, request):
        continents = Continent.objects.prefetch_related('country_set')
        partners = Partner.objects.values('uuid', 'name')
        ucl_universities = (
            Entity.objects
            .filter(partnerships__isnull=False)
            .prefetch_related(
                Prefetch(
                    'parent_of',
                    queryset=EntityVersion.objects
                        .filter(entity__partnerships_labo__isnull=False, end_date__isnull=True)
                        .distinct()
                ),
                Prefetch(
                    'parent_of__entity',
                    queryset=Entity.objects
                        .annotate(
                            most_recent_acronym=Subquery(
                                EntityVersion.objects
                                    .filter(entity=OuterRef('pk'))
                                    .order_by('-start_date')
                                    .values('acronym')[:1]
                            ),
                        )
                )
            )
            .annotate(
                most_recent_acronym=Subquery(
                    EntityVersion.objects
                        .filter(entity=OuterRef('pk'))
                        .order_by('-start_date')
                        .values('acronym')[:1]
                ),
            )
            .distinct()
            .order_by('most_recent_acronym')
        )
        supervisors = Person.objects.filter(
            Q(management_entities__isnull=False) | Q(partnerships_supervisor__isnull=False)
        ).order_by('last_name', 'first_name')
        education_fields = PartnershipYearEducationField.objects.values('uuid', 'label')

        data = {
            'continents': ContinentConfigurationSerializer(continents, many=True).data,
            'partners': PartnerConfigurationSerializer(partners, many=True).data,
            'ucl_universities': UCLUniversityConfigurationSerializer(ucl_universities, many=True).data,
            'supervisors': SupervisorConfigurationSerializer(supervisors, many=True).data,
            'education_fields': EducationFieldConfigurationSerializer(education_fields, many=True).data,
        }
        return Response(data)


class PartnersListView(generics.ListAPIView):
    serializer_class = PartnerSerializer
    permission_classes = (AllowAny,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = PartnerFilter

    def get_queryset(self):
        academic_year = PartnershipConfiguration.get_configuration().get_current_academic_year_for_api()

        return (
            Partner.objects
            .select_related('partner_type', 'contact_address__country')
            .annotate(
                current_academic_year=Value(academic_year.id, output_field=models.AutoField()),
                partnerships_count=Count('partnerships'),
            )
        )


class PartnershipsMixinView(GenericAPIView):
    serializer_class = PartnershipSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        academic_year = PartnershipConfiguration.get_configuration().get_current_academic_year_for_api()

        return (
            Partnership.objects
            .select_related(
                'supervisor',
            ).prefetch_related(
                'contacts',
                Prefetch(
                    'partner',
                    queryset=Partner.objects
                        .select_related('partner_type', 'contact_address__country')
                        .annotate(partnerships_count=Count('partnerships'))
                ),
                Prefetch(
                    'ucl_university',
                    queryset=Entity.objects
                    .annotate(
                        most_recent_acronym=Subquery(
                            EntityVersion.objects
                                .filter(entity=OuterRef('pk'))
                                .order_by('-start_date')
                                .values('acronym')[:1]
                        ),
                        most_recent_title=Subquery(
                            EntityVersion.objects
                                .filter(entity=OuterRef('pk'))
                                .order_by('-start_date')
                                .values('title')[:1]
                        ),
                    )
                ),
                Prefetch(
                    'ucl_university_labo',
                    queryset=Entity.objects
                    .annotate(
                        most_recent_acronym=Subquery(
                            EntityVersion.objects
                                .filter(entity=OuterRef('pk'))
                                .order_by('-start_date')
                                .values('acronym')[:1]
                        ),
                        most_recent_title=Subquery(
                            EntityVersion.objects
                                .filter(entity=OuterRef('pk'))
                                .order_by('-start_date')
                                .values('title')[:1]
                        ),
                    )
                ),
                Prefetch(
                    'years',
                    queryset=(
                        PartnershipYear.objects
                        .prefetch_related(
                            'education_fields', 'education_levels', 'entities', 'offers'
                        ).filter(academic_year=academic_year)
                    ),
                    to_attr='current_year_for_api',
                ),
            )
        ).annotate(
            current_academic_year=Value(academic_year.id, output_field=models.AutoField()),
            validity_end_year=Subquery(
                AcademicYear.objects
                .filter(
                    partnership_agreements_end__partnership=OuterRef('pk'),
                    partnership_agreements_end__status=PartnershipAgreement.STATUS_VALIDATED
                )
                .order_by('-end_date')
                .values('year')[:1]
            ),
            validity_years=Concat(
                Value(academic_year.year),
                Value('-'),
                'validity_end_year',
                output_field=models.CharField()
            ),
            agreement_status=Subquery(
                PartnershipAgreement.objects
                .filter(
                    partnership=OuterRef('pk'),
                    start_academic_year__year__lte=academic_year.year,
                    end_academic_year__year__gte=academic_year.year,
                )
                .order_by('-end_academic_year__year')
                .values('status')[:1]
            ),
            sector_most_recent_acronym=Subquery(
                EntityVersion.objects
                    .filter(entity__parent_of__entity=OuterRef('ucl_university__pk'))
                    .order_by('-start_date')
                    .values('acronym')[:1]
            )
        )


class PartnershipsListView(PartnershipsMixinView, generics.ListAPIView):
    filter_backends = [DjangoFilterBackend]
    filterset_class = PartnershipFilter


class PartnershipsRetrieveView(PartnershipsMixinView, generics.RetrieveAPIView):
    lookup_field = 'uuid'
