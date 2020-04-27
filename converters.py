from partnership.models import PartnershipType


class PartnershipTypeConverter:
    regex = '\w+'

    def to_python(self, value):
        if value not in PartnershipType.get_names():
            raise ValueError("%s value: is not a valid partnership type")
        return getattr(PartnershipType, value)

    def to_url(self, value):
        return value.name
