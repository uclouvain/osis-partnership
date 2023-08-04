import uuid
from datetime import timedelta

import factory
from django.utils import timezone

from base.models.enums.organization_type import ACADEMIC_PARTNER
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.entity_version_address import (
    EntityVersionAddressFactory
)
from base.tests.factories.organization import OrganizationFactory
from partnership.models import Partner, PartnerEntity, PartnerTag

__all__ = [
    'PartnerFactory',
    'PartnerTagFactory',
    'PartnerEntityFactory',
]


class PartnerTagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PartnerTag
        django_get_or_create = ('value',)

    value = factory.Sequence(lambda n: 'PartnerTag-é-{0}-{1}'.format(n, uuid.uuid4()))


class PartnerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Partner

    is_valid = True
    organization = factory.SubFactory(
        OrganizationFactory,
        name=factory.Sequence(lambda n: 'Partner-é-{0}'.format(n)),
        type=ACADEMIC_PARTNER,
    )
    pic_code = factory.Sequence(lambda n: 'pic_code-é-{0}-{1}'.format(n, uuid.uuid4()))
    erasmus_code = factory.Sequence(lambda n: 'erasmus_code-é-{0}-{1}'.format(n, uuid.uuid4()))

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
            extra_kwargs = {}
            obj._entity = obj.organization.entity_set.first()
            if not obj._entity:
                extra_kwargs['entity__organization'] = obj.organization
            else:
                extra_kwargs['entity'] = obj._entity
            obj._entity_version = EntityVersionFactory(
                start_date=start or (timezone.now() - timedelta(days=365)),
                end_date=end,
                parent=None,
                **extra_kwargs
            )
            if not obj._entity:
                obj._entity = obj._entity_version.entity
                obj.organization.entity_set.add(obj._entity_version.entity)

    @factory.post_generation
    def contact_address(obj, create, extracted, **kwargs):
        if create and (extracted or kwargs):
            EntityVersionAddressFactory(
                entity_version_id=obj._entity_version.pk,
                **kwargs,
            )


class PartnerEntityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PartnerEntity

    name = factory.Sequence(lambda n: 'PartnerEntity-é-{0}'.format(n))
    entity = factory.SubFactory(EntityWithVersionFactory)

    @factory.post_generation
    def partner(obj, create, extracted, **kwargs):
        if create:
            partner = extracted or PartnerFactory()
            version = obj.entity.most_recent_entity_version
            if not version.parent_id:
                version.parent = partner.organization.entity_set.first()
                version.save()
            obj.entity.organization = partner.organization
            obj.entity.save()
