from rest_framework import serializers

__all__ = [
    'FinancingSerializer',
]


class FinancingSerializer(serializers.Serializer):
    name = serializers.CharField(source='__str__')
    iso_code = serializers.CharField()
    financing_name = serializers.CharField()
    financing_url = serializers.CharField()
