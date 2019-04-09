from django.db.models.aggregates import Count
from django.db.models.expressions import Subquery, OuterRef
from django.db.models.query import Prefetch
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.person import Person
from partnership.api.serializers import PartnerSerializer, PartnershipSerializer, ContinentConfigurationSerializer, \
    PartnerConfigurationSerializer, UCLUniversityConfigurationSerializer, SupervisorConfigurationSerializer, \
    EducationFieldConfigurationSerializer
from partnership.models import Partner, Partnership, PartnershipYearEducationField, PartnershipYear, \
    PartnershipConfiguration
from reference.models.continent import Continent


class ConfigurationView(APIView):

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
        supervisors = Person.objects.filter(management_entities__isnull=False).order_by('last_name', 'first_name')
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
    queryset = (
        Partner.objects
        .select_related('partner_type', 'contact_address__country')
        .annotate(partnerships_count=Count('partnerships'))
    )
    serializer_class = PartnerSerializer


class PartnershipsListView(generics.ListAPIView):
    serializer_class = PartnershipSerializer

    def get_queryset(self):
        academic_year = PartnershipConfiguration.get_configuration().get_current_academic_year_for_api()

        return (
            Partnership.objects
            .select_related(
                'supervisor',
            ).prefetch_related(
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
        )
