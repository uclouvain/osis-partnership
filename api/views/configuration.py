from django.conf import settings
from django.contrib.postgres.aggregates import StringAgg
from django.db.models import Exists, F, OuterRef, Prefetch, Subquery
from django.utils.translation import get_language
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.enums.entity_type import FACULTY, SECTOR
from base.utils.cte import CTESubquery
from partnership.api.serializers import (
    ContinentConfigurationSerializer,
    EducationFieldConfigurationSerializer, PartnerConfigurationSerializer,
    UCLUniversityConfigurationSerializer,
)
from partnership.models import (
    Financing, Partner, PartnershipAgreement,
    PartnershipConfiguration,
)
from reference.models.continent import Continent
from reference.models.country import Country
from reference.models.domain_isced import DomainIsced


class ConfigurationView(APIView):

    permission_classes = (AllowAny,)

    def get(self, request):
        current_year = PartnershipConfiguration.get_configuration().get_current_academic_year_for_api()

        continents = Continent.objects.prefetch_related(
            Prefetch(
                'country_set',
                queryset=Country.objects.annotate(
                    cities=StringAgg('entityversionaddress__city', ';', distinct=True)
                )
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
            .values('uuid', 'organization__name')
        )

        last_version = EntityVersion.objects.filter(
            entity=OuterRef('pk')
        ).order_by('-start_date')

        # Get entities with their sector and faculty (if exists)
        cte = EntityVersion.objects.with_children(entity_id=OuterRef('pk'))
        qs = cte.join(
            EntityVersion, id=cte.col.id
        ).with_cte(cte).order_by('-start_date')

        ucl_universities = (
            Entity.objects
            .annotate(
                most_recent_acronym=Subquery(last_version.values('acronym')[:1]),
                most_recent_title=Subquery(last_version.values('title')[:1]),
                sector_acronym=CTESubquery(
                    qs.filter(entity_type=SECTOR).values('acronym')[:1]
                ),
                faculty_acronym=CTESubquery(
                    qs.exclude(
                        entity_id=(OuterRef('pk')),
                    ).filter(entity_type=FACULTY).values('acronym')[:1]
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
            .order_by(
                'sector_acronym',
                F('faculty_acronym').asc(nulls_first=True),
                'most_recent_acronym',
            )
        )

        label = 'title_fr' if get_language() == settings.LANGUAGE_CODE_FR else 'title_en'
        education_fields = (
            DomainIsced.objects
            .filter(partnershipyear__academic_year=current_year)
            .distinct()
            .values('uuid', label)
        )
        fundings = (
             Financing.objects
             .filter(academic_year=current_year)
             .values_list('type__name', flat=True)
             .distinct('type__name')
             .order_by('type__name')
        )

        data = {
            'continents': ContinentConfigurationSerializer(continents, many=True).data,
            'partners': PartnerConfigurationSerializer(partners, many=True).data,
            'ucl_universities': UCLUniversityConfigurationSerializer(ucl_universities, many=True).data,
            'education_fields': EducationFieldConfigurationSerializer(education_fields, many=True).data,
            'fundings': list(fundings),
        }
        return Response(data)
