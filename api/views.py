from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from base.models.entity import Entity
from base.models.person import Person
from partnership.api.serializers import PartnerSerializer, PartnershipSerializer, ContinentConfigurationSerializer, \
    PartnerConfigurationSerializer, UCLUniversityConfigurationSerializer, SupervisorConfigurationSerializer, \
    EducationFieldConfigurationSerializer
from partnership.models import Partner, Partnership, PartnershipYearEducationField
from reference.models.continent import Continent


class ConfigurationView(APIView):

    def get(self, request):
        continents = Continent.objects.prefetch_related('country_set')
        partners = Partner.objects.values('uuid', 'name')
        ucl_universities = Entity.objects.filter(partnerships__isnull=False)
        supervisors = Person.objects.filter(academic_responsible__isnull=False).order_by('last_name', 'first_name')
        education_fields = PartnershipYearEducationField.objects.values('uuid', 'label')

        data = {
            'continents': ContinentConfigurationSerializer(continents).data,
            'partners': PartnerConfigurationSerializer(partners).data,
            'ucl_universities': UCLUniversityConfigurationSerializer(ucl_universities).data,
            'supervisors': SupervisorConfigurationSerializer(supervisors).data,
            'education_fields': EducationFieldConfigurationSerializer(education_fields).data,
        }
        return Response(data)


class PartnersListView(generics.ListAPIView):
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer


class PartnershipsListView(generics.ListAPIView):
    queryset = Partnership.objects.all()
    serializer_class = PartnershipSerializer
