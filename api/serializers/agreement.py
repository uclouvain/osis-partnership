from django.utils.html import format_html
from django.utils.safestring import mark_safe
from rest_framework import serializers

from partnership.models import PartnershipAgreement
from partnership.utils import academic_years


class PartnershipAgreementAdminSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedRelatedField(
        view_name='partnerships:detail',
        source='partnership',
        read_only=True,
    )
    country = serializers.ReadOnlyField(source='country_name')
    city = serializers.ReadOnlyField()
    supervisor = serializers.CharField(source='partnership.get_supervisor')
    partner = serializers.CharField(
        source='partnership.partner.organization.name'
    )
    entities_acronyms = serializers.SerializerMethodField()
    academic_years = serializers.SerializerMethodField()
    status = serializers.CharField(source='get_status_display')

    class Meta:
        model = PartnershipAgreement
        fields = [
            'url', 'country', 'city', 'supervisor', 'partner',
            'entities_acronyms', 'academic_years', 'status',
        ]

    @staticmethod
    def get_entities_acronyms(agreement):
        entities = []
        if agreement.partnership_ucl_sector_most_recent_acronym:
            entities.append(format_html(
                '<abbr title="{0}">{1}</abbr>',
                agreement.partnership_ucl_sector_most_recent_title,
                agreement.partnership_ucl_sector_most_recent_acronym,
            ))
        if agreement.partnership_ucl_faculty_most_recent_acronym:
            entities.append(format_html(
                '<abbr title="{0}">{1}</abbr>',
                agreement.partnership_ucl_faculty_most_recent_title,
                agreement.partnership_ucl_faculty_most_recent_acronym,
            ))
        if agreement.partnership_ucl_entity_most_recent_acronym:
            entities.append(format_html(
                '<abbr title="{0}">{1}</abbr>',
                agreement.partnership_ucl_entity_most_recent_title,
                agreement.partnership_ucl_entity_most_recent_acronym,
            ))
        return mark_safe(' / '.join(entities))

    @staticmethod
    def get_academic_years(agreement):
        return academic_years(
            agreement.start_academic_year,
            agreement.end_academic_year,
        )
