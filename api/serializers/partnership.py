from django.conf import settings
from django.utils.translation import get_language
from rest_framework import serializers

from partnership.models import (
    Partnership, MediaType,
    AgreementStatus,
)
from .contact import ContactSerializer
from .media import MediaSerializer, AgreementMediaSerializer
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
        source='ucl_sector_most_recent_acronym',
        allow_null=True,
    )
    ucl_faculty = serializers.SerializerMethodField()
    ucl_entity = EntitySerializer()
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
        source='ucl_entity.uclmanagement_entity.contact_out_url', allow_null=True)
    out_education_levels = serializers.SerializerMethodField()
    out_entities = serializers.SerializerMethodField()
    out_university_offers = serializers.SerializerMethodField()
    out_funding = serializers.SerializerMethodField(method_name='get_funding')
    out_partner_contacts = ContactSerializer(source='contacts', many=True)
    out_course_catalogue = serializers.SerializerMethodField()
    out_summary_tables = serializers.SerializerMethodField()

    in_contact = serializers.SerializerMethodField()
    in_portal = serializers.URLField(
        source='ucl_entity.uclmanagement_entity.contact_in_url',
        allow_null=True,
    )

    staff_contact = serializers.SerializerMethodField()
    staff_funding = serializers.SerializerMethodField()
    staff_partner_contacts = ContactSerializer(source='contacts', many=True)

    class Meta:
        model = Partnership
        fields = [
            'uuid', 'url', 'partner', 'supervisor', 'ucl_entity',
            'ucl_faculty',
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
        education_fields = self._get_current_year_attr(partnership, 'education_fields')
        if education_fields is None:
            return None

        label = 'title_fr' if get_language() == settings.LANGUAGE_CODE_FR else 'title_en'
        return [('{0.%s} ({0.code})' % label).format(field)
                for field in education_fields.all()]

    def get_status(self, partnership):
        if partnership.agreement_status is None:
            return None
        return {
            'status': AgreementStatus.get_value(partnership.agreement_status),
            # annotation on the queryset
            'valid_years': partnership.validity_years,
            # annotation on the queryset
        }

    def get_bilateral_agreements(self, partnership):
        return [
            AgreementMediaSerializer(agreement, context=self.context).data
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
        if not hasattr(partnership.ucl_entity, 'uclmanagement_entity'):
            return {}
        ume = partnership.ucl_entity.uclmanagement_entity
        administrative_person = ume.administrative_responsible

        email = ume.contact_out_email
        if email is None:
            email = administrative_person.email

        person = ume.contact_out_person
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
        if not hasattr(partnership.ucl_entity, 'uclmanagement_entity'):
            return {}
        ume = partnership.ucl_entity.uclmanagement_entity

        return {
            'fr': {
                'text': ume.course_catalogue_text_fr,
                'url': ume.course_catalogue_url_fr,
            },
            'en': {
                'text': ume.course_catalogue_text_en,
                'url': ume.course_catalogue_url_en,
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
        if not hasattr(partnership.ucl_entity, 'uclmanagement_entity'):
            return None

        ume = partnership.ucl_entity.uclmanagement_entity
        administrative_person = ume.administrative_responsible
        email = ume.contact_in_email

        if email is None:
            email = getattr(administrative_person, 'email', None)
        person = ume.contact_in_person

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
        if not partnership.current_year_for_api:
            return None
        if not self._get_current_year_attr(partnership, 'eligible'):
            return None
        if not partnership.funding_name:
            return None
        return {
            'name': partnership.funding_name,
            'url': partnership.funding_url,
        }

    def get_staff_contact(self, partnership):
        if not hasattr(partnership.ucl_entity, 'uclmanagement_entity'):
            return None
        ume = partnership.ucl_entity.uclmanagement_entity
        administrative_person = ume.administrative_responsible
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

    @staticmethod
    def get_ucl_faculty(partnership):
        return {
            'acronym': partnership.ucl_faculty_most_recent_acronym,
            'title': partnership.ucl_faculty_most_recent_title,
        }


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
