import factory

from partnership.models import Partnership, PartnershipTag, PartnershipType
from .partner import PartnerFactory
from .partnership_year import PartnershipYearFactory

__all__ = [
    'PartnershipFactory',
    'PartnershipTagFactory',
]


class PartnershipTagFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnershipTag

    value = factory.Sequence(lambda n: 'PartnershipTag-é-{0}'.format(n))


class PartnershipFactory(factory.DjangoModelFactory):
    class Meta:
        model = Partnership

    partner = factory.SubFactory(PartnerFactory)
    partnership_type = PartnershipType.MOBILITY.name

    ucl_entity = factory.SubFactory(
        'base.tests.factories.entity.EntityFactory',
        organization=None,
        country=factory.SelfAttribute('..partner.contact_address.country'),
    )

    @factory.post_generation
    def tags(obj, create, extracted, **kwargs):
        if create and extracted is not None:
            obj.tags.set(extracted)

    @factory.post_generation
    def contacts(obj, create, extracted, **kwargs):
        if create and extracted is not None:
            obj.contacts.set(extracted)

    @factory.post_generation
    def years(obj, create, extracted, **kwargs):
        if create:
            if extracted is not None:
                obj.years.set(extracted)
            else:
                obj.years.set([PartnershipYearFactory(partnership=obj)])
