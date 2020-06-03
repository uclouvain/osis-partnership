import factory

from partnership.models import Partnership, PartnershipTag
from .contact import ContactFactory
from .partner import PartnerEntityFactory, PartnerFactory
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
    partner_entity = factory.SubFactory(
        PartnerEntityFactory,
        partner=factory.SelfAttribute('..partner'),
    )

    ucl_entity = factory.SubFactory(
        'base.tests.factories.entity.EntityFactory',
        country=factory.SelfAttribute('..partner.contact_address.country'),
    )

    author = factory.SubFactory('base.tests.factories.person.PersonFactory')

    @factory.post_generation
    def tags(obj, create, extracted, **kwargs):
        if create:
            if extracted:
                obj.tags.set(extracted)
            else:
                obj.tags.set([PartnershipTagFactory(), PartnershipTagFactory()])

    @factory.post_generation
    def contacts(obj, create, extracted, **kwargs):
        if create:
            if extracted:
                obj.contacts.set(extracted)
            else:
                obj.contacts.set([ContactFactory(), ContactFactory()])

    @factory.post_generation
    def years(obj, create, extracted, **kwargs):
        if create:
            if extracted is not None:
                obj.years.set(extracted)
            else:
                obj.years.set([PartnershipYearFactory(partnership=obj)])
