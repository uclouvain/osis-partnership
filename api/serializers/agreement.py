from django.utils.html import format_html
from django.utils.safestring import mark_safe
from rest_framework import serializers

from partnership.models import PartnershipAgreement


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
    coverage = serializers.SerializerMethodField()
    status = serializers.CharField(source='get_status_display')

    class Meta:
        model = PartnershipAgreement
        fields = [
            'url', 'country', 'city', 'supervisor', 'partner',
            'entities_acronyms', 'coverage', 'status',
        ]

    @staticmethod
    def get_entities_acronyms(agreement):
        entities = []
        for i in range(1, len(agreement.acronym_path)):
            entities.append(format_html(
                '<abbr title="{0}">{1}</abbr>',
                agreement.title_path[i],
                agreement.acronym_path[i],
            ))
        return mark_safe(' / '.join(entities))

    @staticmethod
    def get_coverage(agreement):
        if agreement.partnership.is_mobility:
            return "{} > {}".format(
                agreement.start_academic_year,
                agreement.end_academic_year,
            )
        return "{:%d/%m/%Y} > {:%d/%m/%Y}".format(
            agreement.start_date,
            agreement.end_date,
        )
