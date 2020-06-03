import factory

from partnership.models import (
    PartnershipMission,
    PartnershipSubtype,
    PartnershipType, PartnershipYear,
)

__all__ = [
    'PartnershipMissionFactory',
    'PartnershipSubtypeFactory',
    'PartnershipYearFactory',
]


class PartnershipYearFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnershipYear
        django_get_or_create = ('academic_year', 'partnership',)

    academic_year = factory.SubFactory(
        'base.tests.factories.academic_year.AcademicYearFactory',
        year=2020,  # BUG: OP-348 - dirty fix
    )
    partnership = factory.SubFactory('partnership.tests.factories.PartnershipFactory')

    @factory.post_generation
    def missions(obj, create, extracted, **kwargs):
        if create and extracted is not None:
            obj.missions.set(extracted)


class PartnershipMissionFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnershipMission

    types = PartnershipType.get_names()
    code = factory.Faker('word')


class PartnershipSubtypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnershipSubtype

    types = PartnershipType.get_names()
    code = factory.Faker('word')
