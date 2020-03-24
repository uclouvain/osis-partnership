from rest_framework import serializers

from partnership.models import PartnershipAgreement
from partnership.utils import academic_years


class PartnershipAgreementAdminSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='partnerships:detail',
        source='partnership'
    )
    country = serializers.CharField(
        source='partnership.partner.contact_address.country',
    )
    city = serializers.CharField(
        source='partnership.partner.contact_address.city',
    )
    supervisor = serializers.CharField(source='partnership.get_supervisor')
    partner = serializers.CharField(source='partnership.partner.name')
    entities_acronyms = serializers.CharField(
        source='partnership.entities_acronyms'
    )
    academic_years = serializers.SerializerMethodField()
    status = serializers.CharField(source='get_status_display')

    class Meta:
        model = PartnershipAgreement
        fields = [
            'url', 'country', 'city', 'supervisor', 'partner',
            'entities_acronyms', 'academic_years', 'status',
        ]

    @staticmethod
    def get_academic_years(agreement):
        return academic_years(
            agreement.start_academic_year,
            agreement.end_academic_year,
        )
