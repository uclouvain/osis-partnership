from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.utils.translation import get_language
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from partnership.models import (
    Partnership, MediaType,
    AgreementStatus,
)
from .contact import ContactSerializer
from .media import MediaSerializer, AgreementMediaSerializer
from .partner import PartnerDetailSerializer
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
    partner = PartnerDetailSerializer()
    type = serializers.ReadOnlyField(source='get_partnership_type_display')
    partner_entity = serializers.CharField(
        source='partner_entity.name',
        allow_null=True,
    )
    supervisor = serializers.CharField(
        source='get_supervisor',
        allow_null=True,
    )
    ucl_sector = serializers.CharField(source='acronym_path.1', allow_null=True)
    ucl_faculty = serializers.SerializerMethodField()
    ucl_entity = EntitySerializer()
    is_sms = serializers.SerializerMethodField()
    is_smp = serializers.SerializerMethodField()
    is_smst = serializers.SerializerMethodField()
    is_sta = serializers.SerializerMethodField()
    is_stt = serializers.SerializerMethodField()

    missions = serializers.SerializerMethodField()
    subtype = serializers.SerializerMethodField()
    id_number = serializers.SerializerMethodField()
    project_title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

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
    out_useful_links = serializers.SerializerMethodField()
    funding_program = serializers.SerializerMethodField()

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
            'uuid', 'url', 'partner', 'supervisor', 'type', 'partnership_type',
            'ucl_sector', 'ucl_faculty', 'ucl_entity',
            'is_sms', 'is_smp', 'is_smst', 'is_sta', 'is_stt',

            'missions', 'subtype', 'description', 'id_number', 'project_title',
            'funding_program',

            'education_fields', 'status', 'partner_entity', 'medias',
            'bilateral_agreements',
            # OUT
            'out_education_levels', 'out_entities', 'out_university_offers',
            'out_contact', 'out_portal', 'out_funding',
            'out_partner_contacts', 'out_course_catalogue',
            'out_summary_tables', 'out_useful_links',
            # IN
            'in_contact', 'in_portal',
            # STAFF
            'staff_contact', 'staff_funding',
            'staff_partner_contacts',
        ]

    @staticmethod
    def _get_current_year_attr(partnership, attr):
        try:
            return getattr(partnership.current_year_for_api[0], attr)
        except IndexError:  # pragma: no cover
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

    def get_missions(self, partnership):
        missions = self._get_current_year_attr(partnership, 'missions')
        return ', '.join([mission.label for mission in missions.all()])

    def get_description(self, partnership):
        return self._get_current_year_attr(partnership, 'description')

    def get_id_number(self, partnership):
        return self._get_current_year_attr(partnership, 'id_number')

    def get_project_title(self, partnership):
        return self._get_current_year_attr(partnership, 'project_title')

    def get_subtype(self, partnership):
        subtype = self._get_current_year_attr(partnership, 'subtype')
        if subtype:
            return subtype.label

    def get_education_fields(self, partnership):
        education_fields = self._get_current_year_attr(partnership, 'education_fields')
        if education_fields is None:  # pragma: no cover
            return None

        label = 'title_fr' if get_language() == settings.LANGUAGE_CODE_FR else 'title_en'
        return [('{0.%s} ({0.code})' % label).format(field)
                for field in education_fields.all()]

    def get_status(self, partnership):
        if partnership.is_mobility:
            return {
                'status': AgreementStatus.VALIDATED.value,
                # annotation on the queryset
                'valid_years': partnership.validity_years,
            }
        value = _('status_ongoing')
        if partnership.agreement_end:  # pragma: no cover
            threshold = partnership.agreement_end + timedelta(days=365 * 5)
            today = timezone.now().date()
            if today < partnership.agreement_end:
                value = _('status_ongoing')
            elif today < threshold:
                value = _('status_finished')
            elif threshold < today:
                value = _('status_archived')
        return {
            'status': value,
            # annotations on the queryset
            'start_date': partnership.agreement_start.strftime('%d/%m/%Y')
            if partnership.agreement_start else '',
            'end_date': partnership.agreement_end.strftime('%d/%m/%Y')
            if partnership.agreement_end else '',
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
        if education_levels is None:  # pragma: no cover
            return None
        return [level.code for level in education_levels.all()]

    def get_out_entities(self, partnership):
        entities = self._get_current_year_attr(partnership, 'entities')
        if entities is None:  # pragma: no cover
            return None
        return [EntitySerializer(entity).data for entity in entities.all()]

    def get_out_university_offers(self, partnership):
        offers = self._get_current_year_attr(partnership, 'offers')
        if offers is None:  # pragma: no cover
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

    @staticmethod
    def get_public_media(partnership, media_type):
        medias = [
            MediaSerializer(media).data for media in partnership.medias.all()
            if (media.is_visible_in_portal and media.type is not None
                and media.type.code == media_type)
        ]
        medias += [
            MediaSerializer(media).data
            for media in partnership.partner.medias.all()
            if (media.is_visible_in_portal and media.type is not None
                and media.type.code == media_type)
        ]
        return medias

    def get_out_summary_tables(self, partnership):
        return self.get_public_media(partnership, MediaType.SUMMARY_TABLE)

    def get_out_useful_links(self, partnership):
        return self.get_public_media(partnership, MediaType.USEFUL_LINK)

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
        funding_source = self._get_current_year_attr(partnership, 'funding_source')
        if funding_source:
            return {'name': str(funding_source), 'url': ''}
        eligible = self._get_current_year_attr(partnership, 'eligible')
        if partnership.is_mobility and eligible and partnership.funding_name:
            return {
                'name': partnership.funding_name,
                'url': partnership.funding_url,
            }

    def get_funding_program(self, partnership):
        label = ''
        funding_program = self._get_current_year_attr(partnership, 'funding_program')
        if funding_program:
            label += str(funding_program)
        funding_type = self._get_current_year_attr(partnership, 'funding_type')
        if funding_type:
            label += ' / ' + str(funding_type)
        return label

    def get_staff_contact(self, partnership):
        if not hasattr(partnership.ucl_entity, 'uclmanagement_entity'):
            return None
        ume = partnership.ucl_entity.uclmanagement_entity
        contact = {
            'email': ume.administrative_responsible.email,
            'title': None,
            'first_name': ume.administrative_responsible.first_name,
            'last_name': ume.administrative_responsible.last_name,
            'phone': ume.administrative_responsible.phone,
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
        if len(partnership.acronym_path) < 3:
            return {}
        return {
            'acronym': partnership.acronym_path[2],
            'title': partnership.title_path[2],
        }


class PartnershipAdminSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='partnerships:detail',
    )
    country = serializers.ReadOnlyField(source='country_name')
    city = serializers.ReadOnlyField()
    supervisor = serializers.CharField(source='get_supervisor')
    partner = serializers.CharField(source='partner.organization.name')
    type = serializers.CharField(source='get_partnership_type_display')

    class Meta:
        model = Partnership
        fields = [
            'uuid', 'url', 'partner', 'supervisor', 'country', 'city',
            'entities_acronyms', 'validity_end', 'type'
        ]
