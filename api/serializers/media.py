from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.reverse import reverse

from partnership.models import Media

__all__ = [
    'MediaSerializer',
    'AgreementMediaSerializer',
]


class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = ['name', 'url']


class AgreementMediaSerializer(serializers.Serializer):
    url = serializers.SerializerMethodField()
    name = serializers.CharField(source='media.name')

    @extend_schema_field(OpenApiTypes.STR)
    def get_url(self, agreement):
        media = agreement.media
        if media.file.name:  # pragma: no cover
            # TODO: Fix when authentication is done in ESB (use already X-Forwarded-Host) / Shibb
            url = reverse('partnerships:agreements:download_media', args=(agreement.partnership_id, agreement.pk))
            return '{scheme}://{host}{path}'.format(
                scheme=self.context["request"].scheme,
                host=self.context["request"].META["HTTP_HOST"],
                path=url,
            )
        return media.url
