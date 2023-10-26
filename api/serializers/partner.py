import datetime
import json

from django.db import transaction
from rest_framework import serializers

from base.models.entity_version import EntityVersion
from base.models.entity_version_address import EntityVersionAddress
from base.models.enums.organization_type import ORGANIZATION_TYPE
from base.models.organization import Organization
from partnership.models import Partner, EntityProxy

__all__ = [
    'PartnerListSerializer',
    'PartnerAdminSerializer',
    'PartnerDetailSerializer',
]

from partnership.utils import generate_partner_prefix
from reference.models.country import Country


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


class InternshipPartnerSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(choices=ORGANIZATION_TYPE, source="organization.type")
    name = serializers.CharField(max_length=255, source="organization.name")
    website = serializers.CharField(max_length=255, source="entity.website")
    street_number = serializers.CharField(max_length=12, required=False, source="contact_address.street_number")
    street = serializers.CharField(max_length=255, source="contact_address.street")
    postal_code = serializers.CharField(max_length=32, required=False, source="contact_address.postal_code")
    city = serializers.CharField(max_length=255, source="contact_address.city")
    country = serializers.CharField(max_length=2, source="contact_address.country.iso_code")
    latitude = serializers.FloatField(min_value=-90, max_value=90, required=False)
    longitude = serializers.FloatField(min_value=-180, max_value=180, required=False)

    # Read only
    start_date = serializers.CharField(source="organization.start_date", read_only=True)
    end_date = serializers.CharField(source="organization.end_date", read_only=True)

    class Meta:
        model = Partner
        fields = [
            'uuid', 'is_valid', 'organisation_identifier', 'size', 'is_public', 'is_nonprofit',
            'erasmus_code', 'pic_code', 'contact_type', 'phone', 'email',
            # Organization
            'name', 'type',
            # Entity
            'website', 'start_date', 'end_date',
            # EntityAddress
            'street_number', 'street', 'postal_code', 'city', 'country',
            'latitude', 'longitude',
        ]
        read_only_fields = [
            'is_valid', 'start_date', 'end_date', 'erasmus_code', 'pic_code', 'phone', 'email', 'contact_type',
        ]

    def validate_country(self, value):
        try:
            return Country.objects.get(iso_code__iexact=value)
        except Country.DoesNotExist:
            raise serializers.ValidationError("Country not found")

    @transaction.atomic()
    def create(self, validated_data):
        # Create organization
        organization = Organization.objects.create(
            name=validated_data['organization']['name'],
            type=validated_data['organization']['type'],
            prefix=generate_partner_prefix(validated_data['organization']['name'])
        )

        # Entity
        entity = EntityProxy.objects.create(
            website=validated_data['entity']['website'],
            organization=organization,
        )

        # EntityVersion
        last_version = EntityVersion.objects.create(
            title=entity.organization.name,
            entity=entity,
            acronym=entity.organization.prefix,
            parent=None,
            start_date=datetime.date.today(),
        )

        # Partner
        partner = Partner.objects.create(
            organisation_identifier=validated_data.get('organisation_identifier', ''),
            size=validated_data['size'],
            is_public=validated_data['is_public'],
            is_nonprofit=validated_data['is_nonprofit'],
            organization=organization,
            author=self.context['request'].user.person,
        )

        # EntityVersionAddress
        longitude = validated_data['contact_address'].get("longitude")
        latitude = validated_data['contact_address'].get("latitude")
        if latitude and longitude:
            location = f'SRID=4326;POINT({longitude} {latitude})'
        else:
            location = None
        EntityVersionAddress.objects.create(
            entity_version=last_version,
            is_main=True,
            street_number=validated_data['contact_address'].get('street_number', ''),
            street=validated_data['contact_address'].get('street', ''),
            postal_code=validated_data['contact_address'].get('postal_code', ''),
            state=validated_data['contact_address'].get('state', ''),
            city=validated_data['contact_address'].get('city', ''),
            country=validated_data['contact_address'].get('country', {}).get('iso_code'),
            location=location,
        )

        return partner
