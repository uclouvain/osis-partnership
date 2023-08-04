import factory

from partnership.models import (
    Financing, FundingProgram, FundingSource, FundingType,
)

__all__ = [
    'FinancingFactory',
    'FundingTypeFactory',
    'FundingProgramFactory',
    'FundingSourceFactory',
]


class FundingSourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FundingSource

    name = factory.Faker('word')


class FundingProgramFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FundingProgram

    name = factory.Faker('word')
    source = factory.SubFactory(FundingSourceFactory)


class FundingTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FundingType

    name = factory.Faker('word')
    url = factory.Faker('url')
    program = factory.SubFactory(FundingProgramFactory)


class FinancingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Financing

    type = factory.SubFactory(FundingTypeFactory)
