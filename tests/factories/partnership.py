import factory

from base.models.enums.organization_type import ACADEMIC_PARTNER
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

    partner_entity = factory.SubFactory(
        'base.tests.factories.entity.EntityWithVersionFactory',
        organization__type=ACADEMIC_PARTNER,
    )
    partnership_type = PartnershipType.MOBILITY.name

    ucl_entity = factory.SubFactory(
        'base.tests.factories.entity.EntityWithVersionFactory',
        organization=None,
        version__acronym="SO"
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
            if extracted is None:
                obj.years.set([
                    PartnershipYearFactory(partnership=obj, **kwargs),
                ])
            elif extracted:
                obj.years.set(extracted)

    @factory.post_generation
    def missions(obj, create, extracted, **kwargs):
        if create and extracted is not None:
            obj.missions.set(extracted)

    @factory.post_generation
    def partner(obj, create, extracted, **kwargs):
        if create and extracted is None and not hasattr(obj.partner_entity.organization, 'partner'):
            PartnerFactory(
                organization=obj.partner_entity.organization,
                **kwargs,
            )
