from django.contrib.postgres.aggregates import StringAgg
from django.db.models import Exists, OuterRef, Prefetch, Subquery, Q, Value
from django.db.models.functions import Concat
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.person import Person
from partnership.api.serializers import ContinentConfigurationSerializer, \
    PartnerConfigurationSerializer, UCLUniversityConfigurationSerializer, \
    SupervisorConfigurationSerializer, EducationFieldConfigurationSerializer
from partnership.models import PartnershipConfiguration, Partner, \
    PartnershipAgreement, PartnershipYearEducationField, Financing
from reference.models.continent import Continent
from reference.models.country import Country


class ConfigurationView(APIView):

    permission_classes = (AllowAny,)

    def get(self, request):
        current_year = PartnershipConfiguration.get_configuration().get_current_academic_year_for_api()

        continents = Continent.objects.prefetch_related(
            Prefetch(
                'country_set',
                queryset=Country.objects.annotate(cities=StringAgg('address__city', ';', distinct=True))
            )
        )
        partners = (
            Partner.objects
            .annotate(
                has_in=Exists(
                    PartnershipAgreement.objects.filter(
                        partnership__partner=OuterRef('pk'),
                        start_academic_year__year__lte=current_year.year,
                        end_academic_year__year__gte=current_year.year,
                    )
                )
            )
            .filter(has_in=True)
            .values('uuid', 'name')
        )
        ucl_universities = (
            Entity.objects
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
                                    .annotate(name=Concat('acronym', Value(' - '), 'title'))
                                    .values('name')[:1]
                            ),
                        )
                )
            )
            .annotate(
                most_recent_acronym=Subquery(
                    EntityVersion.objects
                        .filter(entity=OuterRef('pk'))
                        .order_by('-start_date')
                        .annotate(name=Concat('acronym', Value(' - '), 'title'))
                        .values('name')[:1]
                ),
                has_in=Exists(
                    PartnershipAgreement.objects.filter(
                        partnership=OuterRef('partnerships'),
                        start_academic_year__year__lte=current_year.year,
                        end_academic_year__year__gte=current_year.year,
                    )
                )
            )
            .filter(has_in=True)
            .distinct()
            .order_by('most_recent_acronym')
        )
        supervisors = Person.objects.filter(
            Q(management_entities__isnull=False) | Q(partnerships_supervisor__isnull=False)
        ).order_by('last_name', 'first_name').distinct()
        education_fields = (
            PartnershipYearEducationField.objects
            .filter(partnershipyear__academic_year=current_year)
            .distinct()
            .values('uuid', 'label')
        )
        fundings = (
             Financing.objects
             .filter(academic_year=current_year)
             .values_list('name', flat=True)
             .distinct('name')
             .order_by('name')
        )

        data = {
            'continents': ContinentConfigurationSerializer(continents, many=True).data,
            'partners': PartnerConfigurationSerializer(partners, many=True).data,
            'ucl_universities': UCLUniversityConfigurationSerializer(ucl_universities, many=True).data,
            'supervisors': SupervisorConfigurationSerializer(supervisors, many=True).data,
            'education_fields': EducationFieldConfigurationSerializer(education_fields, many=True).data,
            'fundings': list(fundings),
        }
        return Response(data)
