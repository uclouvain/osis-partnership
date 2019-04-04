from rest_framework import serializers

from base.models.entity import Entity
from base.models.person import Person
from partnership.models import Partner, PartnershipYearEducationField
from reference.models.continent import Continent
from reference.models.country import Country


class CountryConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['name', 'iso_code']


class ContinentConfigurationSerializer(serializers.ModelSerializer):
    countries = CountryConfigurationSerializer(many=True, source='country_set')

    class Meta:
        model = Continent
        fields = ['name', 'countries']


class PartnerConfigurationSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='uuid')
    label = serializers.CharField(source='name')

    class Meta:
        model = Partner
        fields = ['value', 'label']


class UCLUniversityLaboConfigurationSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='uuid')
    label = serializers.CharField(source='most_recent_acronym')

    class Meta:
        model = Entity
        fields = ['value', 'label']


class UCLUniversityConfigurationSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='uuid')
    label = serializers.CharField(source='most_recent_acronym')
    ucl_university_labos = UCLUniversityLaboConfigurationSerializer(source='TODO')

    class Meta:
        model = Entity
        fields = ['value', 'label', 'ucl_university_labos']


class SupervisorConfigurationSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='uuid')
    label = serializers.CharField(source='__str__')

    class Meta:
        model = Person
        fields = ['value', 'label']


class EducationFieldConfigurationSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='uuid')
    label = serializers.CharField(source='label')

    class Meta:
        model = PartnershipYearEducationField
        fields = ['value', 'label']


class PartnerSerializer(serializers.ModelSerializer):
    pass


class PartnershipSerializer(serializers.ModelSerializer):
    pass
