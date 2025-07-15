from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.utils.translation import get_language
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from partnership.models import (
    MediaType,
    AgreementStatus,
    PartnershipPartnerRelation,
)
from .contact import ContactSerializer
from .media import MediaSerializer, AgreementMediaSerializer
from .partner import PartnerDetailSerializer
from .entity import EntitySerializer

__all__ = [
    'PartnershipPartnerRelationSerializer',
    'PartnershipPartnerRelationAdminSerializer',
]


# Used for schema generation only
class FundingSerializer(serializers.Serializer):
    name = serializers.CharField()
    url = serializers.CharField()


# Used for schema generation only
class UclFacultySerializer(serializers.Serializer):
    acronym = serializers.CharField()
    title = serializers.CharField()


class PartnershipPartnerRelationSerializer(serializers.ModelSerializer):
    uuid = serializers.ReadOnlyField(source='partnership.uuid')
    url = serializers.HyperlinkedRelatedField(
        view_name='partnership_api_v1:retrieve',
        lookup_field='uuid',
        source='partnership',
        read_only=True,
    )
    partner = PartnerDetailSerializer(
        source='entity.organization.partner_prefetched',
    )
    type = serializers.ReadOnlyField(
        source='partnership.get_partnership_type_display',
    )
    partnership_type = serializers.ReadOnlyField(
        source='partnership.partnership_type',
    )
    partner_entity = serializers.CharField(
        source='entity.partnerentity.name',
        allow_null=True,
    )
    partner_entities = serializers.SerializerMethodField()
    supervisor = serializers.CharField(
        source='partnership.get_supervisor',
        allow_null=True,
    )
    ucl_sector = serializers.SerializerMethodField()
    ucl_faculty = serializers.SerializerMethodField()
    ucl_entity = EntitySerializer(source='partnership.ucl_entity')
    is_sms = serializers.SerializerMethodField()
    is_smp = serializers.SerializerMethodField()
    is_smst = serializers.SerializerMethodField()
    is_sta = serializers.SerializerMethodField()
    is_stt = serializers.SerializerMethodField()

    subtype = serializers.ReadOnlyField(source='partnership.subtype.label')
    description = serializers.ReadOnlyField(source='partnership.description')
    id_number = serializers.ReadOnlyField(source='partnership.id_number')
    project_title = serializers.ReadOnlyField(source='partnership.project_title')

    missions = serializers.SerializerMethodField()

    education_fields = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    bilateral_agreements = serializers.SerializerMethodField()
    medias = MediaSerializer(many=True, source='partnership.medias')

    out_contact = serializers.SerializerMethodField()
    out_portal = serializers.URLField(
        source='partnership.ucl_entity.uclmanagement_entity.contact_out_url',
        allow_null=True,
    )
    out_education_levels = serializers.SerializerMethodField()
    out_entities = serializers.SerializerMethodField()
    out_university_offers = serializers.SerializerMethodField()
    out_funding = serializers.SerializerMethodField(method_name='get_funding')
    out_partner_contacts = ContactSerializer(source='partnership.contacts', many=True)
    out_course_catalogue = serializers.SerializerMethodField()
    out_summary_tables = serializers.SerializerMethodField()
    out_useful_links = serializers.SerializerMethodField()
    funding_program = serializers.SerializerMethodField()

    in_contact = serializers.SerializerMethodField()
    in_portal = serializers.URLField(
        source='partnership.ucl_entity.uclmanagement_entity.contact_in_url',
        allow_null=True,
    )

    staff_contact = serializers.SerializerMethodField()
    staff_funding = serializers.SerializerMethodField()
    staff_partner_contacts = ContactSerializer(source='partnership.contacts', many=True)

    class Meta:
        model = PartnershipPartnerRelation
        fields = [
            'uuid', 'url', 'partner', 'supervisor', 'type', 'partnership_type',
            'ucl_sector', 'ucl_faculty', 'ucl_entity',
            'is_sms', 'is_smp', 'is_smst', 'is_sta', 'is_stt',

            'missions', 'subtype', 'description', 'id_number', 'project_title',
            'funding_program',

            'education_fields', 'status', 'partner_entity', 'medias',
            'partner_entities',
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

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_sms(self, rel):
        return self._get_current_year_attr(rel.partnership, 'is_sms')

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_smp(self, rel):
        return self._get_current_year_attr(rel.partnership, 'is_smp')

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_smst(self, rel):
        return self._get_current_year_attr(rel.partnership, 'is_smst')

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_sta(self, rel):
        return self._get_current_year_attr(rel.partnership, 'is_sta')

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_stt(self, rel):
        return self._get_current_year_attr(rel.partnership, 'is_stt')

    @staticmethod
    @extend_schema_field(OpenApiTypes.STR)
    def get_missions(rel):
        return ', '.join([mission.label for mission in rel.partnership.missions.all()])

    @extend_schema_field(serializers.ListSerializer(child=serializers.CharField()))
    def get_education_fields(self, rel):
        education_fields = self._get_current_year_attr(rel.partnership, 'education_fields')
        if education_fields is None:  # pragma: no cover
            return None

        label = 'title_fr' if get_language() == settings.LANGUAGE_CODE_FR else 'title_en'
        return [('{0.%s} ({0.code})' % label).format(field)
                for field in education_fields.all()]

    @extend_schema_field({
        "type": "object",
        "properties": {
            "status": {"type": "string"},
            "start_date": {"type": "string"},
            "end_date": {"type": "string"},
        },
    })
    def get_status(self, rel):
        partnership = rel.partnership
        if partnership.is_mobility:
            return {
                'status': AgreementStatus.VALIDATED.value,
                # annotation on the queryset
                'valid_years': rel.validity_years,
            }
        value = _('status_ongoing')
        if rel.agreement_end:  # pragma: no cover
            threshold = rel.agreement_end + timedelta(days=365 * 5)
            today = timezone.now().date()
            if today < rel.agreement_end:
                value = _('status_ongoing')
            elif today < threshold:
                value = _('status_finished')
            elif threshold < today:
                value = _('status_archived')
        if partnership.is_course or partnership.is_doctorate:
            return {
                'status': value,
                # annotations on the queryset
                'start_date': rel.start_year,
                'end_date': rel.end_year,
            }
        else:
            return {
                'status': value,
                'start_date': partnership.start_date.strftime('%d/%m/%Y')
                if partnership.start_date else '',
                'end_date': partnership.end_date.strftime('%d/%m/%Y')
                if partnership.end_date else '',
            }

    @extend_schema_field(AgreementMediaSerializer(many=True))
    def get_bilateral_agreements(self, rel):
        return [
            AgreementMediaSerializer(agreement, context=self.context).data
            for agreement in rel.partnership.valid_current_agreements
            if agreement.media.is_visible_in_portal
        ]

    @extend_schema_field(serializers.ListSerializer(child=serializers.CharField()))
    def get_out_education_levels(self, rel):
        education_levels = self._get_current_year_attr(
            rel.partnership, 'education_levels'
        )
        if education_levels is None:  # pragma: no cover
            return None
        return [level.code for level in education_levels.all()]

    @extend_schema_field(EntitySerializer(many=True))
    def get_out_entities(self, rel):
        entities = self._get_current_year_attr(rel.partnership, 'entities')
        if entities is None:  # pragma: no cover
            return None
        return [EntitySerializer(entity).data for entity in entities.all()]

    @extend_schema_field(serializers.ListSerializer(child=serializers.CharField()))
    def get_out_university_offers(self, rel):
        offers = self._get_current_year_attr(rel.partnership, 'offers')
        if offers is None:  # pragma: no cover
            return None
        return ['{} - {}'.format(offer.acronym, offer.title)
                for offer in offers.all()]

    @extend_schema_field(ContactSerializer)
    def get_out_contact(self, rel):
        partnership = rel.partnership
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

    @extend_schema_field({
        "type": "object",
        "properties": {
            "fr": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "url": {"type": "string"},
                },
            },
            "en": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "url": {"type": "string"},
                },
            },
        },
    })
    def get_out_course_catalogue(self, rel):
        if not hasattr(rel.partnership.ucl_entity, 'uclmanagement_entity'):
            return {}
        ume = rel.partnership.ucl_entity.uclmanagement_entity

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
    def get_public_media(rel, media_type):
        medias = [
            MediaSerializer(media).data for media in rel.partnership.medias.all()
            if (media.is_visible_in_portal and media.type is not None
                and media.type.code == media_type)
        ]
        medias += [
            MediaSerializer(media).data
            for media in rel.entity.organization.partner_prefetched.medias.all()
            if (media.is_visible_in_portal and media.type is not None
                and media.type.code == media_type)
        ]
        return medias

    @extend_schema_field(MediaSerializer(many=True))
    def get_out_summary_tables(self, rel):
        return self.get_public_media(rel, MediaType.SUMMARY_TABLE)

    @extend_schema_field(MediaSerializer(many=True))
    def get_out_useful_links(self, rel):
        return self.get_public_media(rel, MediaType.USEFUL_LINK)

    @extend_schema_field(ContactSerializer)
    def get_in_contact(self, rel):
        if not hasattr(rel.partnership.ucl_entity, 'uclmanagement_entity'):
            return None

        ume = rel.partnership.ucl_entity.uclmanagement_entity
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

    @extend_schema_field(FundingSerializer)
    def get_funding(self, rel):
        partnership = rel.partnership
        funding_source = self._get_current_year_attr(partnership, 'funding_source')
        if funding_source:
            return {'name': str(funding_source), 'url': ''}
        eligible = self._get_current_year_attr(partnership, 'eligible')
        if partnership.is_mobility and eligible and rel.funding_name:
            return {
                'name': rel.funding_name,
                'url': rel.funding_url,
            }

    @extend_schema_field(FundingSerializer)
    def get_funding_program(self, rel):
        label = ''
        partnership = rel.partnership
        funding_program = self._get_current_year_attr(partnership, 'funding_program')
        if funding_program:
            label += str(funding_program)
        funding_type = self._get_current_year_attr(partnership, 'funding_type')
        if funding_type:
            label += ' / ' + str(funding_type)
        return {
            'name': label,
            'url': funding_type and funding_type.url,
        }

    @extend_schema_field(ContactSerializer)
    def get_staff_contact(self, rel):
        if not hasattr(rel.partnership.ucl_entity, 'uclmanagement_entity'):
            return None
        ume = rel.partnership.ucl_entity.uclmanagement_entity
        contact = {
            'email': ume.administrative_responsible.email,
            'title': None,
            'first_name': ume.administrative_responsible.first_name,
            'last_name': ume.administrative_responsible.last_name,
            'phone': ume.administrative_responsible.phone,
        }
        return contact

    @extend_schema_field(FundingSerializer)
    def get_staff_funding(self, rel):
        funding = self.get_funding(rel)
        if funding is None:
            return None
        funding['url'] = settings.STAFF_FUNDING_URL
        return funding

    @staticmethod
    @extend_schema_field(OpenApiTypes.STR)
    def get_ucl_sector(rel):
        if not rel.partnership.acronym_path or len(rel.partnership.acronym_path) < 2:
            return ''
        return rel.partnership.acronym_path[1]

    @staticmethod
    @extend_schema_field(UclFacultySerializer)
    def get_ucl_faculty(rel):
        if not rel.partnership.acronym_path or len(rel.partnership.acronym_path) < 3:
            return {}
        return {
            'acronym': rel.partnership.acronym_path[2],
            'title': rel.partnership.title_path[2],
        }

    @staticmethod
    @extend_schema_field(serializers.ListSerializer(child=serializers.CharField()))
    def get_partner_entities(rel):
        if rel.partnership.num_partners == 1:
            return []
        return [
            '{} - {}, {}'.format(
                entity.partner_name,
                entity.partner_city,
                entity.partner_country,
            )
            for entity in rel.partnership.partner_entities.all()
        ]


class PartnershipPartnerRelationAdminSerializer(serializers.ModelSerializer):
    uuid = serializers.ReadOnlyField(source='partnership.uuid')
    url = serializers.HyperlinkedRelatedField(
        view_name='partnerships:detail',
        source='partnership',
        read_only=True,
    )
    country = serializers.ReadOnlyField(source='country_name')
    city = serializers.ReadOnlyField()
    supervisor = serializers.CharField(source='partnership.get_supervisor')
    partner = serializers.SerializerMethodField()
    type = serializers.CharField(source='partnership.get_partnership_type_display')
    entities_acronyms = serializers.ReadOnlyField(
        source='partnership.entities_acronyms',
    )
    validity_end = serializers.ReadOnlyField(
        source='partnership.validity_end',
    )

    @staticmethod
    @extend_schema_field(OpenApiTypes.STR)
    def get_partner(rel):
        if rel.partnership.num_partners >= 1 and len(rel.partnership.project_acronym)>0:
            return "{} ({})".format(
                rel.entity.organization.name,
                rel.partnership.project_acronym,
            )
        return rel.entity.organization.name

    class Meta:
        model = PartnershipPartnerRelation
        fields = [
            'uuid', 'url', 'partner', 'supervisor', 'country', 'city',
            'entities_acronyms', 'validity_end', 'type'
        ]
