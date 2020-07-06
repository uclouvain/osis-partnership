import uuid
from datetime import timedelta

import factory
from django.utils import timezone

from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.organization import MainOrganizationFactory
from partnership.models import Partner, PartnerEntity, PartnerTag
from .address import AddressFactory

__all__ = [
    'PartnerFactory',
    'PartnerTagFactory',
    'PartnerEntityFactory',
]


class PartnerTagFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnerTag
        django_get_or_create = ('value',)

    value = factory.Sequence(lambda n: 'PartnerTag-é-{0}-{1}'.format(n, uuid.uuid4()))


class PartnerFactory(factory.DjangoModelFactory):
    class Meta:
        model = Partner

    is_valid = True
    is_ies = factory.Faker('boolean')
    organization = factory.SubFactory(
        MainOrganizationFactory,
        name=factory.Sequence(lambda n: 'Partner-é-{0}'.format(n)),
    )
    pic_code = factory.Sequence(lambda n: 'pic_code-é-{0}-{1}'.format(n, uuid.uuid4()))
    erasmus_code = factory.Sequence(lambda n: 'erasmus_code-é-{0}-{1}'.format(n, uuid.uuid4()))

    contact_address = factory.SubFactory(AddressFactory)

    email = factory.Faker('email')
    phone = factory.Faker('phone_number')
    is_nonprofit = factory.Faker('boolean')
    is_public = factory.Faker('boolean')

    @factory.post_generation
    def tags(obj, create, extracted, **kwargs):
        if create and extracted is not None:
            obj.tags.set(extracted)

    @factory.post_generation
    def dates(obj, create, extracted, start=None, end=None, **kwargs):
        if create:
            entity_version = EntityVersionFactory(
                entity__organization=obj.organization,
                start_date=start or (timezone.now() - timedelta(days=365)),
                end_date=end,
                parent=None,
            )
            obj.organization.entity_set.add(entity_version.entity)

    @factory.post_generation
    def entities(obj, create, extracted, **kwargs):
        if create and extracted is not None:
            obj.entities.set(extracted)


class PartnerEntityFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnerEntity

    name = factory.Sequence(lambda n: 'PartnerEntity-é-{0}'.format(n))
    entity_version = factory.SubFactory(EntityVersionFactory, parent=None)

    @factory.post_generation
    def partner(obj, create, extracted, **kwargs):
        if create:
            partner = extracted or PartnerFactory()
            if not obj.entity_version.parent_id:
                obj.entity_version.parent = partner.organization.entity_set.first()
                obj.entity_version.save()
            obj.entity_version.entity.organization = partner.organization
            obj.entity_version.entity.save()
