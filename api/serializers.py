from rest_framework import serializers

from base.models.entity import Entity
from base.models.person import Person
from partnership.models import Partner, PartnershipYearEducationField, Partnership
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
    ucl_university_labos = serializers.SerializerMethodField()

    class Meta:
        model = Entity
        fields = ['value', 'label', 'ucl_university_labos']

    def get_ucl_university_labos(self, instance):
        entities = (entity_version.entity for entity_version in instance.parent_of.all())
        return UCLUniversityLaboConfigurationSerializer(entities, many=True).data


class SupervisorConfigurationSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='uuid')
    label = serializers.CharField(source='__str__')

    class Meta:
        model = Person
        fields = ['value', 'label']


class EducationFieldConfigurationSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='uuid')
    label = serializers.CharField()

    class Meta:
        model = PartnershipYearEducationField
        fields = ['value', 'label']


class PartnerSerializer(serializers.ModelSerializer):
    partner_type = serializers.CharField(source='partner_type.value')
    city = serializers.CharField(source='contact_address.city')
    country = serializers.CharField(source='contact_address.country.name')

    class Meta:
        model = Partner
        fields = ['name', 'erasmus_code', 'partner_type', 'city', 'country']


class PartnershipSerializer(serializers.ModelSerializer):
    partner = PartnerSerializer()


    class Meta:
        model = Partnership
        fields = [
            'partner', 'education_field', 'ucl_university', 'ucl_university_labo', 'supervisor',
            'mobility_type', 'status',
            # OUT
            'out_education_level', 'out_entity', 'out_university_offer', 'out_contact',
            'out_portal', 'out_funding', 'out_partner_contact',
            # IN
            'in_contact', 'in_portal', 'staff_contact_name',
            # STAFF
            'staff_partner_contact', 'staff_funding',
        ]
