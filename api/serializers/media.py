from rest_framework import serializers

from partnership.models import Media

__all__ = [
    'MediaSerializer',
]


class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = ['name', 'url']
