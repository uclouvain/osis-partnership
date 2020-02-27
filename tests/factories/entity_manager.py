import factory

from partnership.models import PartnershipEntityManager

__all__ = ['PartnershipEntityManagerFactory']


class PartnershipEntityManagerFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnershipEntityManager

    person = factory.SubFactory('base.tests.factories.person.PersonFactory')
    entity = factory.SubFactory('base.tests.factories.entity.EntityFactory')
