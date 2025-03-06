import factory

from base.models.enums.organization_type import ACADEMIC_PARTNER
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from partnership.models import Partnership, PartnershipTag, PartnershipType, PartnershipConfiguration
from .partner import PartnerFactory
from .partnership_year import PartnershipYearFactory

__all__ = [
    'PartnershipFactory',
    'PartnershipTagFactory',
]


class PartnershipTagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PartnershipTag

    value = factory.Sequence(lambda n: 'PartnershipTag-é-{0}'.format(n))


class PartnershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Partnership

    partnership_type = PartnershipType.MOBILITY.name

    ucl_entity = factory.SubFactory(
        'base.tests.factories.entity.EntityWithVersionFactory',
        organization=None,
        version__acronym="SO"
    )

    @factory.post_generation
    def partner_entity(obj, create, extracted, **kwargs):
        if create:
            if extracted is None:
                kwargs.setdefault('organization__type', ACADEMIC_PARTNER)
                extracted = EntityWithVersionFactory(**kwargs)
            obj.partner_entities.add(extracted)
            obj.partner_entity = extracted

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



class PartnershipConfigurationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PartnershipConfiguration

    partnership_creation_update_min_year = factory.SubFactory(AcademicYearFactory)

