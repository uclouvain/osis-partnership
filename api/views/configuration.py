from django.conf import settings
from django.contrib.postgres.aggregates import StringAgg
from django.db.models import Prefetch, Value
from django.utils.translation import get_language
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from base.models.education_group_year import EducationGroupYear
from partnership.api.serializers import (
    ContinentConfigurationSerializer,
    OfferSerializer,
    PartnerConfigurationSerializer,
    UCLUniversityConfigurationSerializer,
)
from partnership.api.serializers.configuration import (
    EducationLevelSerializer,
    PartnershipTypeSerializer, ConfigurationSerializer,
)
from partnership.models import (
    EntityProxy,
    Partner,
    PartnerTag,
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

    @extend_schema(
        responses=ConfigurationSerializer,
    )
    def get(self, request):
        config = PartnershipConfiguration.get_configuration()
        current_year = config.get_current_academic_year_for_api()

        continents = Continent.objects.prefetch_related(
            Prefetch(
                'country_set',
                queryset=Country.objects.annotate(
                    cities=StringAgg('entityversionaddress__city', ';', distinct=True, default=Value(''))
                )
            )
        )
        partners = (
            Partner.objects
            .having_partnerships()
            .distinct('pk')
            .order_by('pk')
            .values('uuid', 'organization__name')
        )

        # Get UCL entity parents which children have a partnership
        ucl_universities = (
            EntityProxy.objects
            .ucl_entities_parents()
            .with_title()
            .with_acronym_path()
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
                .distinct('pk')
                .order_by('pk')
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
             .of_partners_having_partnerships()
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
