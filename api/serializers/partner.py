import json
from rest_framework import serializers

from partnership.models import Partner

__all__ = [
    'PartnerListSerializer',
    'PartnerAdminSerializer',
    'PartnerDetailSerializer',
]


class PartnerListSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='organization.name')
    city = serializers.ReadOnlyField()
    country = serializers.ReadOnlyField(source='country_name')
    country_iso = serializers.CharField(source='country_iso_code')
    partnerships_count = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

    class Meta:
        model = Partner
        fields = [
            'uuid', 'name', 'city', 'country', 'country_iso',
            'location', 'partnerships_count',
        ]

    def get_partnerships_count(self, obj):
        return self.context['counts'][obj.pk]

    def get_location(self, obj):
        if obj.location:
            return json.loads(obj.location.json)


class PartnerDetailSerializer(PartnerListSerializer):
    partner_type = serializers.CharField(source='organization.get_type_display')
    website = serializers.CharField()

    class Meta:
        model = Partner
        fields = [
            'uuid', 'name', 'website', 'erasmus_code', 'partner_type',
            'city', 'country', 'country_iso',
        ]


class PartnerAdminSerializer(PartnerListSerializer):
    partner_type = serializers.CharField(source='organization.get_type_display')
    url = serializers.HyperlinkedIdentityField(
        view_name='partnerships:partners:detail',
    )
    partnerships_count = serializers.IntegerField()

    class Meta:
        model = Partner
        fields = [
            'name', 'erasmus_code', 'partner_type', 'city', 'country',
            'partnerships_count', 'is_actif', 'is_valid', 'url', 'id',
        ]
