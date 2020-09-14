from django.conf import settings
from django.contrib.postgres.aggregates import StringAgg
from django.db.models import Exists, F, OuterRef, Prefetch, Subquery
from django.utils.translation import get_language
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from base.models.education_group_year import EducationGroupYear
from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.utils.cte import CTESubquery
from partnership.api.serializers import (
    ContinentConfigurationSerializer,
    OfferSerializer,
    PartnerConfigurationSerializer,
    UCLUniversityConfigurationSerializer,
)
from partnership.api.serializers.configuration import (
    EducationLevelSerializer,
    PartnershipTypeSerializer,
)
from partnership.models import (
    Partner,
    PartnerTag,
    PartnershipAgreement,
    PartnershipConfiguration,
    PartnershipTag,
    PartnershipType,
    PartnershipYearEducationLevel,
)
from partnership.views import FundingAutocompleteView
from reference.models.continent import Continent
from reference.models.country import Country


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

        ucl_universities = (
            Entity.objects
            .annotate(
                most_recent_title=Subquery(last_version.values('title')[:1]),
                acronym_path=CTESubquery(
                    EntityVersion.objects.with_acronym_path(
                        entity_id=OuterRef('pk'),
                    ).values('acronym_path')[:1]
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
            .order_by('acronym_path')
        )

        # label = 'title_fr' if get_language() == settings.LANGUAGE_CODE_FR else 'title_en'
        # education_fields = (
        #     DomainIsced.objects
        #     .filter(partnershipyear__academic_year=current_year)
        #     .distinct()
        #     .values('uuid', label)
        # )
        education_levels = (
            PartnershipYearEducationLevel.objects
                .filter(partnerships_years__academic_year=current_year,
                        partnerships_years__partnership__isnull=False)
                .distinct()
                .values('code', 'label')
        )

        label = 'title' if get_language() == settings.LANGUAGE_CODE_FR else 'title_english'
        year_offers = EducationGroupYear.objects.filter(
            partnerships__isnull=False,
        ).values('uuid', 'acronym', label).distinct().order_by('acronym', label)

        view = FundingAutocompleteView()
        view.q = ''
        fundings = view.get_list()

        tags = (
             PartnershipTag.objects
             .filter(partnerships__isnull=False)
             .values_list('value', flat=True)
             .distinct('value')
             .order_by('value')
        )
        partner_tags = (
             PartnerTag.objects
             .filter(partners__partnerships__isnull=False)
             .values_list('value', flat=True)
             .distinct('value')
             .order_by('value')
        )

        data = {
            'continents': ContinentConfigurationSerializer(continents, many=True).data,
            'partners': PartnerConfigurationSerializer(partners, many=True).data,
            'ucl_universities': UCLUniversityConfigurationSerializer(ucl_universities, many=True).data,
            # 'education_fields': EducationFieldConfigurationSerializer(education_fields, many=True).data,
            'education_levels': EducationLevelSerializer(education_levels, many=True).data,
            'fundings': list(fundings),
            'partnership_types': PartnershipTypeSerializer(PartnershipType.all(), many=True).data,
            'tags': list(tags),
            'partner_tags': list(partner_tags),
            'offers': OfferSerializer(year_offers, many=True).data,
        }
        return Response(data)
