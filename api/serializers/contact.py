from rest_framework import serializers

from partnership.models import Contact

__all__ = [
    'ContactSerializer',
]


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['title', 'first_name', 'last_name', 'phone', 'email']
