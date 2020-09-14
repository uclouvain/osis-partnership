from django.conf import settings
from django.utils.translation import get_language
from rest_framework import serializers

from base.models.education_group_year import EducationGroupYear
from base.models.entity import Entity
from base.models.person import Person
from partnership.models import Partner, PartnershipYearEducationLevel
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
    'EducationLevelSerializer',
    'OfferSerializer',
    'PartnershipTypeSerializer',
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
    label = serializers.CharField(source='organization__name')

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
    label = serializers.SerializerMethodField()

    class Meta:
        model = Entity
        fields = ['value', 'label']

    @staticmethod
    def get_label(result):
        parts = result.acronym_path[1:] if result.acronym_path[1:] else result.acronym_path
        return '{} - {}'.format(' / '.join(parts), result.most_recent_title)


class SupervisorConfigurationSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='uuid')
    label = serializers.CharField(source='__str__')

    class Meta:
        model = Person
        fields = ['value', 'label']


class EducationLevelSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='code')
    label = serializers.CharField()

    class Meta:
        model = PartnershipYearEducationLevel
        fields = ['value', 'label']


class EducationFieldConfigurationSerializer(serializers.ModelSerializer):  # pragma: no cover
    value = serializers.CharField(source='uuid')
    label = serializers.SerializerMethodField()

    class Meta:
        model = DomainIsced
        fields = ['value', 'label']

    @staticmethod
    def get_label(result):
        label = 'title_fr' if get_language() == settings.LANGUAGE_CODE_FR else 'title_en'
        return result[label]


class OfferSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='uuid')
    label = serializers.SerializerMethodField()

    class Meta:
        model = EducationGroupYear
        fields = ['value', 'label']

    @staticmethod
    def get_label(result):
        label = 'title' if get_language() == settings.LANGUAGE_CODE_FR else 'title_english'
        return "{} - {}".format(result['acronym'], result[label])


class PartnershipTypeSerializer(serializers.Serializer):
    value = serializers.CharField(source='name')
    label = serializers.CharField(source='value')
