from rest_framework import serializers

from base.models.entity import Entity
from base.models.person import Person
from partnership.models import Partner
from reference.models.continent import Continent
from reference.models.country import Country
from reference.models.domain_isced import DomainIsced

__all__ = [
    'CountryConfigurationSerializer',
    'ContinentConfigurationSerializer',
    'PartnerConfigurationSerializer',
    'UCLUniversityConfigurationSerializer',
    'UCLUniversityLaboConfigurationSerializer',
    'EducationFieldConfigurationSerializer',
    'SupervisorConfigurationSerializer',
]


class CountryConfigurationSerializer(serializers.ModelSerializer):
    cities = serializers.SerializerMethodField()

    class Meta:
        model = Country
        fields = ['name', 'iso_code', 'cities']

    def get_cities(self, country):
        return country.cities.split(';')


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

    class Meta:
        model = Entity
        fields = ['value', 'label']


class SupervisorConfigurationSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='uuid')
    label = serializers.CharField(source='__str__')

    class Meta:
        model = Person
        fields = ['value', 'label']


class EducationFieldConfigurationSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='uuid')
    label = serializers.CharField(source='title_en')

    class Meta:
        model = DomainIsced
        fields = ['value', 'label']
