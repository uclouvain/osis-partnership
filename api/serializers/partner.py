from rest_framework import serializers

from partnership.models import Partner

__all__ = [
    'PartnerSerializer',
]


class PartnerSerializer(serializers.ModelSerializer):
    partner_type = serializers.CharField(source='partner_type.value')
    city = serializers.CharField(source='contact_address.city')
    country = serializers.CharField(source='contact_address.country.name')
    country_iso = serializers.CharField(
        source='contact_address.country.iso_code'
    )
    partnerships_count = serializers.IntegerField()

    class Meta:
        model = Partner
        fields = [
            'uuid', 'name', 'website', 'erasmus_code', 'partner_type',
            'city', 'country', 'country_iso', 'partnerships_count',
        ]
