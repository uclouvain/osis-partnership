from rest_framework import serializers

from base.models.entity import Entity

__all__ = [
    'EntitySerializer',
]


class EntitySerializer(serializers.ModelSerializer):
    """ acronym and title must be annotated for this serializer """

    acronym = serializers.CharField()
    title = serializers.CharField()

    class Meta:
        model = Entity
        fields = ['acronym', 'title']
