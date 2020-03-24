from django.conf import settings
from rest_framework import serializers

from partnership.models import Partnership, MediaType, Financing
from .contact import ContactSerializer
from .media import MediaSerializer
from .partner import PartnerSerializer
from .entity import EntitySerializer

__all__ = [
    'PartnershipSerializer',
    'PartnershipAdminSerializer',
]


class PartnershipSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='partnership_api_v1:partnerships:retrieve',
        lookup_field='uuid',
    )
    partner = PartnerSerializer()
    partner_entity = serializers.CharField(
        source='partner_entity.name',
        allow_null=True,
    )
    supervisor = serializers.CharField(
        source='get_supervisor',
        allow_null=True,
    )
    ucl_sector = serializers.CharField(
        source='sector_most_recent_acronym',
        allow_null=True,
    )
    ucl_university = EntitySerializer()
    ucl_university_labo = EntitySerializer()
    is_sms = serializers.SerializerMethodField()
    is_smp = serializers.SerializerMethodField()
    is_smst = serializers.SerializerMethodField()
    is_sta = serializers.SerializerMethodField()
    is_stt = serializers.SerializerMethodField()
    education_fields = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    bilateral_agreements = serializers.SerializerMethodField()
    medias = MediaSerializer(many=True)

    out_contact = serializers.SerializerMethodField()
    out_portal = serializers.URLField(
        source='ucl_management_entity.contact_out_url', allow_null=True)
    out_education_levels = serializers.SerializerMethodField()
    out_entities = serializers.SerializerMethodField()
    out_university_offers = serializers.SerializerMethodField()
    out_funding = serializers.SerializerMethodField(method_name='get_funding')
    out_partner_contacts = ContactSerializer(source='contacts', many=True)
    out_course_catalogue = serializers.SerializerMethodField()
    out_summary_tables = serializers.SerializerMethodField()

    in_contact = serializers.SerializerMethodField()
    in_portal = serializers.URLField(
        source='ucl_management_entity.contact_in_url',
        allow_null=True,
    )

    staff_contact = serializers.SerializerMethodField()
    staff_funding = serializers.SerializerMethodField()
    staff_partner_contacts = ContactSerializer(source='contacts', many=True)

    class Meta:
        model = Partnership
        fields = [
            'uuid', 'url', 'partner', 'supervisor', 'ucl_university',
            'ucl_university_labo',
            'ucl_sector', 'is_sms', 'is_smp', 'is_smst', 'is_sta', 'is_stt',
            'education_fields', 'status', 'partner_entity', 'medias',
            'bilateral_agreements',
            # OUT
            'out_education_levels', 'out_entities', 'out_university_offers',
            'out_contact', 'out_portal', 'out_funding',
            'out_partner_contacts', 'out_course_catalogue',
            'out_summary_tables',
            # IN
            'in_contact', 'in_portal',
            # STAFF
            'staff_contact', 'staff_funding',
            'staff_partner_contacts',
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
        education_fields = self._get_current_year_attr(partnership,
                                                       'education_fields')
        if education_fields is None:
            return None
        return ['{0} ({1})'.format(field.label, field.code) for field in
                education_fields.all()]

    def get_status(self, partnership):
        if partnership.agreement_status is None:
            return None
        return {
            'status': partnership.agreement_status,
            # annotation on the queryset
            'valid_years': partnership.validity_years,
            # annotation on the queryset
        }

    def get_bilateral_agreements(self, partnership):
        return [
            MediaSerializer(agreement.media).data
            for agreement in partnership.valid_current_agreements
            if agreement.media.is_visible_in_portal
        ]

    def get_out_education_levels(self, partnership):
        education_levels = self._get_current_year_attr(partnership,
                                                       'education_levels')
        if education_levels is None:
            return None
        return [level.code for level in education_levels.all()]

    def get_out_entities(self, partnership):
        entities = self._get_current_year_attr(partnership, 'entities')
        if entities is None:
            return None
        return [EntitySerializer(entity).data for entity in entities.all()]

    def get_out_university_offers(self, partnership):
        offers = self._get_current_year_attr(partnership, 'offers')
        if offers is None:
            return None
        return ['{} - {}'.format(offer.acronym, offer.title) for offer in
                offers.all()]

    def get_out_contact(self, partnership):
        administrative_person = getattr(partnership.ucl_management_entity,
                                        'administrative_responsible', None)
        email = getattr(partnership.ucl_management_entity, 'contact_out_email',
                        None)
        if email is None:
            email = getattr(administrative_person, 'email', None)
        person = getattr(partnership.ucl_management_entity,
                         'contact_out_person', None)
        if person is None:
            person = administrative_person

        contact = {
            'email': email,
            'title': None,
            'first_name': None,
            'last_name': None,
            'phone': None,
        }
        if person is not None:
            contact['first_name'] = person.first_name
            contact['last_name'] = person.last_name
            contact['phone'] = person.phone
        return contact

    def get_out_course_catalogue(self, partnership):
        return {
            'fr': {
                'text': getattr(partnership.ucl_management_entity,
                                'course_catalogue_text_fr', None),
                'url': getattr(partnership.ucl_management_entity,
                               'course_catalogue_url_fr', None),
            },
            'en': {
                'text': getattr(partnership.ucl_management_entity,
                                'course_catalogue_text_en', None),
                'url': getattr(partnership.ucl_management_entity,
                               'course_catalogue_url_en', None),
            }
        }

    def get_out_summary_tables(self, partnership):
        medias = [
                     MediaSerializer(media).data
                     for media in partnership.medias.all()
                     if media.is_visible_in_portal
                        and media.type is not None
                        and media.type.code == MediaType.SUMMARY_TABLE
                 ] + [
                     MediaSerializer(media).data
                     for media in partnership.partner.medias.all()
                     if media.is_visible_in_portal
                        and media.type is not None
                        and media.type.code == MediaType.SUMMARY_TABLE
                 ]
        return medias

    def get_in_contact(self, partnership):
        administrative_person = getattr(partnership.ucl_management_entity,
                                        'administrative_responsible', None)
        email = getattr(partnership.ucl_management_entity, 'contact_in_email',
                        None)
        if email is None:
            email = getattr(administrative_person, 'email', None)
        person = getattr(partnership.ucl_management_entity,
                         'contact_in_person', None)
        if person is None:
            person = administrative_person

        contact = {
            'email': email,
            'title': None,
            'first_name': None,
            'last_name': None,
            'phone': None,
        }
        if person is not None:
            contact['first_name'] = person.first_name
            contact['last_name'] = person.last_name
            contact['phone'] = person.phone
        return contact

    def get_funding(self, partnership):
        if not partnership.has_valid_agreement_in_current_year:
            return None
        if not self._get_current_year_attr(partnership, 'eligible'):
            return None
        academic_year = self._get_current_year_attr(partnership,
                                                    'academic_year')
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

    def get_staff_contact(self, partnership):
        administrative_person = getattr(partnership.ucl_management_entity,
                                        'administrative_responsible', None)
        if administrative_person is None:
            return None
        contact = {
            'email': administrative_person.email,
            'title': None,
            'first_name': administrative_person.first_name,
            'last_name': administrative_person.last_name,
            'phone': administrative_person.phone,
        }
        return contact

    def get_staff_funding(self, partnership):
        funding = self.get_funding(partnership)
        if funding is None:
            return None
        funding['url'] = settings.STAFF_FUNDING_URL
        return funding


class PartnershipAdminSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='partnerships:detail',
    )
    country = serializers.CharField(
        source='partner.contact_address.country',
    )
    city = serializers.CharField(
        source='partner.contact_address.city',
    )
    supervisor = serializers.CharField(source='get_supervisor')
    partner = serializers.CharField(source='partner.name')

    class Meta:
        model = Partnership
        fields = [
            'uuid', 'url', 'partner', 'supervisor', 'country', 'city',
            'entities_acronyms', 'validity_end',
        ]
