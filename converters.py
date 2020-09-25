from partnership.models import (
    PartnershipType,
    FundingProgram,
    FundingSource,
    FundingType,
)


class PartnershipTypeConverter:
    regex = '\w+'

    def to_python(self, value):
        if value not in PartnershipType.get_names():
            raise ValueError("%s value: is not a valid partnership type")
        return getattr(PartnershipType, value)

    def to_url(self, value):
        return value.name


class FundingModelConverter:
    regex = '(source|program|type)'
    mapping = {
        'source': FundingSource,
        'program': FundingProgram,
        'type': FundingType,
    }

    def to_python(self, value):
        return self.mapping[value]

    def to_url(self, value):
        if isinstance(value, str) and value in self.mapping:
            return value
        return next(k for k, v in self.mapping.items() if isinstance(value, v))
