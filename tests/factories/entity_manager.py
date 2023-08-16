import factory

from partnership.auth.roles.partnership_manager import PartnershipEntityManager
from partnership.models import PartnershipType

__all__ = ['PartnershipEntityManagerFactory']


class PartnershipEntityManagerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PartnershipEntityManager

    person = factory.SubFactory('base.tests.factories.person.PersonFactory')
    entity = factory.SubFactory(
        'base.tests.factories.entity.EntityFactory',
        organization=None,
    )
    with_child = True
    scopes = [PartnershipType.MOBILITY.name]
