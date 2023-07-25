import factory

from partnership.models import (
    PartnershipYearEducationLevel,
)

__all__ = [
    'PartnershipYearEducationLevelFactory',
]


class PartnershipYearEducationLevelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PartnershipYearEducationLevel

    code = factory.Sequence(lambda n: 'code-é-{0}'.format(n))
    label = factory.Faker('word')
