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

    def get_url(self, agreement):
        media = agreement.media
        if media.file.name:
            url = reverse('partnerships:agreements:download_media', args=(agreement.partnership_id, agreement.pk))
            # TODO: Fix when authentication is done in ESB (use already X-Forwarded-Host) / Shibb
            return self.context["request"].META["HTTP_HOST"] + url
        return media.url
