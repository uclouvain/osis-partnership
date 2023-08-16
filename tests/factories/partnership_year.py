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


class PartnershipYearFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PartnershipYear
        django_get_or_create = ('academic_year', 'partnership',)

    academic_year = factory.SubFactory(
        'base.tests.factories.academic_year.AcademicYearFactory',
        current=True,  # BUG: OP-348 - dirty fix
    )
    partnership = factory.SubFactory(
        'partnership.tests.factories.PartnershipFactory',
        years=[],
    )


class PartnershipMissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PartnershipMission

    types = PartnershipType.get_names()
    code = factory.Faker('word')


class PartnershipSubtypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PartnershipSubtype

    types = PartnershipType.get_names()
    code = factory.Faker('word')
