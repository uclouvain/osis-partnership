import factory

from partnership.models import PartnershipYear

__all__ = ['PartnershipYearFactory']


class PartnershipYearFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnershipYear
        django_get_or_create = ('academic_year', 'partnership',)

    academic_year = factory.SubFactory(
        'base.tests.factories.academic_year.AcademicYearFactory',
        year=2020,  # BUG: OP-348 - dirty fix
    )
    partnership = factory.SubFactory('partnership.tests.factories.PartnershipFactory')
