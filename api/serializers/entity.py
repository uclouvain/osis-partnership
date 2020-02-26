from rest_framework import serializers

from base.models.entity import Entity

__all__ = [
    'EntitySerializer',
]


class EntitySerializer(serializers.ModelSerializer):
    """ most_recent_acronym and most_recent_name must be annotated for this serializer """

    acronym = serializers.CharField(source='most_recent_acronym')
    title = serializers.CharField(source='most_recent_title')

    class Meta:
        model = Entity
        fields = ['acronym', 'title']
