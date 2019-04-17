from rest_framework import serializers

from base.models.entity import Entity
from base.models.person import Person
from partnership.models import Partner, PartnershipYearEducationField, Partnership, Financing, Contact
from reference.models.continent import Continent
from reference.models.country import Country


STAFF_FUNDING_URL = 'https://intranet.uclouvain.be/fr/myucl/administrations/adri/mobilite-du-personnel.html'


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


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['title', 'first_name', 'last_name', 'phone', 'email']


class PartnerSerializer(serializers.ModelSerializer):
    partner_type = serializers.CharField(source='partner_type.value')
    city = serializers.CharField(source='contact_address.city')
    country = serializers.CharField(source='contact_address.country.name')
    partnerships_count = serializers.IntegerField()

    class Meta:
        model = Partner
        fields = ['name', 'erasmus_code', 'partner_type', 'city', 'country', 'partnerships_count']


class PartnershipSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='partnerships_api_v1:partnerships:retrieve',
        lookup_field='uuid',
    )
    partner = PartnerSerializer()
    supervisor = serializers.CharField(source='supervisor.__str__')
    ucl_university = serializers.CharField(source='ucl_university.most_recent_acronym')
    ucl_university_labo = serializers.SerializerMethodField()
    is_sms = serializers.SerializerMethodField()
    is_smp = serializers.SerializerMethodField()
    is_smst = serializers.SerializerMethodField()
    is_sta = serializers.SerializerMethodField()
    is_stt = serializers.SerializerMethodField()
    education_fields = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    out_contact = serializers.SerializerMethodField()
    out_portal = serializers.SerializerMethodField()
    out_education_levels = serializers.SerializerMethodField()
    out_entities = serializers.SerializerMethodField()
    out_university_offers = serializers.SerializerMethodField()
    out_funding = serializers.SerializerMethodField(method_name='get_funding')
    out_partner_contact = ContactSerializer(source='contacts')

    in_contact = serializers.SerializerMethodField()
    in_portal = serializers.SerializerMethodField()

    staff_contact_name = serializers.SerializerMethodField()
    staff_funding = serializers.SerializerMethodField()
    staff_partner_contact = ContactSerializer(source='contacts')

    class Meta:
        model = Partnership
        fields = [
            'url', 'partner', 'supervisor', 'ucl_university', 'ucl_university_labo',
            'is_sms', 'is_smp', 'is_smst', 'is_sta', 'is_stt',
            'education_fields', 'status',
            # OUT
            'out_education_levels', 'out_entities', 'out_university_offers',
            'out_contact', 'out_portal', 'out_funding',
            'out_partner_contact',
            # IN
            'in_contact', 'in_portal',
            # STAFF
            'staff_contact_name', 'staff_funding',
            'staff_partner_contact',
        ]

    def _get_current_year_attr(self, partnership, attr):
        try:
            return getattr(partnership.current_year_for_api[0], attr)
        except IndexError:
            return None

    def get_is_sms(self, partnership):
        return self._get_current_year_attr(partnership, 'is_sms')

    def get_is_smp(self, partnership):
        return self._get_current_year_attr(partnership, 'is_smp')

    def get_is_smst(self, partnership):
        return self._get_current_year_attr(partnership, 'is_smst')

    def get_is_sta(self, partnership):
        return self._get_current_year_attr(partnership, 'is_sta')

    def get_is_stt(self, partnership):
        return self._get_current_year_attr(partnership, 'is_stt')

    def get_education_fields(self, partnership):
        education_fields = self._get_current_year_attr(partnership, 'education_fields')
        if education_fields is None:
            return None
        return ['{0} ({1})'.format(field.label, field.code) for field in education_fields.all()]

    def get_status(self, partnership):
        if partnership.agreement_status is None:
            return None
        return {
            'status': partnership.agreement_status,  # annotation on the queryset
            'valid_years': partnership.validity_years,  # annotation on the queryset
        }

    def get_ucl_university_labo(self, partnership):
        if partnership.ucl_university_labo is None:
            return None
        return partnership.ucl_university_labo.most_recent_acronym

    def get_out_education_levels(self, partnership):
        education_levels = self._get_current_year_attr(partnership, 'education_levels')
        if education_levels is None:
            return None
        return [level.label for level in education_levels.all()]

    def get_out_entities(self, partnership):
        entities = self._get_current_year_attr(partnership, 'entities')
        if entities is None:
            return None
        return [str(entity) for entity in entities.all()]

    def get_out_university_offers(self, partnership):
        offers = self._get_current_year_attr(partnership, 'offers')
        if offers is None:
            return None
        return ['{} - {}'.format(offer.acronym, offer.title) for offer in offers.all()]

    def get_out_contact(self, partnership):
        contact = {
            'email': getattr(partnership.ucl_management_entity, 'contact_out_email', None),
            'name': None,
            'phone': None,
        }
        if getattr(partnership.ucl_management_entity, 'contact_out_person', None) is not None:
            contact['name'] = str(partnership.ucl_management_entity.contact_out_person)
            contact['phone'] = partnership.ucl_management_entity.contact_out_person.phone
        return contact

    def get_out_portal(self, partnership):
        return getattr(partnership.ucl_management_entity, 'contact_out_url', None)

    def get_in_contact(self, partnership):
        contact = {
            'email': getattr(partnership.ucl_management_entity, 'contact_in_email', None),
            'name': None,
            'phone': None,
        }
        if getattr(partnership.ucl_management_entity, 'contact_in_person', None) is not None:
            contact['name'] = str(partnership.ucl_management_entity.contact_in_person)
            contact['phone'] = partnership.ucl_management_entity.contact_in_person.phone
        return contact

    def get_in_portal(self, partnership):
        return getattr(partnership.ucl_management_entity, 'contact_in_url', None)

    def get_funding(self, partnership):
        if not self._get_current_year_attr(partnership, 'eligible'):
            return None
        academic_year = self._get_current_year_attr(partnership, 'academic_year')
        try:
            financing = Financing.objects.get(
                academic_year=academic_year,
                countries=partnership.partner.contact_address.country_id,
            )
        except Financing.DoesNotExist:
            return None
        return {
            'name': financing.name,
            'url': financing.url,
        }

    def get_staff_contact_name(self, partnership):
        supervisor = partnership.get_supervisor()
        if supervisor is None:
            return None
        return str(supervisor)

    def get_staff_funding(self, partnership):
        funding = self.get_funding(partnership)
        if funding is None:
            return None
        funding['url'] = STAFF_FUNDING_URL
        return funding
