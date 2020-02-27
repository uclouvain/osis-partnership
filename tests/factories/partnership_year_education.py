import factory

from partnership.models import (
    PartnershipYearEducationField,
    PartnershipYearEducationLevel,
)

__all__ = [
    'PartnershipYearEducationFieldFactory',
    'PartnershipYearEducationLevelFactory',
]


class PartnershipYearEducationFieldFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnershipYearEducationField

    code = factory.Sequence(lambda n: 'code-é-{0}'.format(n))
    label = factory.Faker('word')


class PartnershipYearEducationLevelFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnershipYearEducationLevel

    code = factory.Sequence(lambda n: 'code-é-{0}'.format(n))
    label = factory.Faker('word')
