import uuid
from datetime import timedelta

import factory
from django.utils import timezone

from partnership.models import PartnerType, PartnerTag, Partner, PartnerEntity
from .address import AddressFactory

__all__ = [
    'PartnerFactory',
    'PartnerTagFactory',
    'PartnerTypeFactory',
    'PartnerEntityFactory',
]


class PartnerTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnerType
        django_get_or_create = ('value',)

    value = factory.Sequence(lambda n: 'PartnerType-{0}'.format(n))


class PartnerTagFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnerTag
        django_get_or_create = ('value',)

    value = factory.Sequence(lambda n: 'PartnerTag-é-{0}-{1}'.format(n, uuid.uuid4()))


class PartnerFactory(factory.DjangoModelFactory):
    class Meta:
        model = Partner
        django_get_or_create = ('partner_type', 'partner_code')

    is_valid = True
    name = factory.Sequence(lambda n: 'Partner-é-{0}'.format(n))
    is_ies = factory.Faker('boolean')
    partner_type = factory.SubFactory(PartnerTypeFactory)
    partner_code = factory.Sequence(lambda n: 'partner_code-é-{0}-{1}'.format(n, uuid.uuid4()))
    pic_code = factory.Sequence(lambda n: 'pic_code-é-{0}-{1}'.format(n, uuid.uuid4()))
    erasmus_code = factory.Sequence(lambda n: 'erasmus_code-é-{0}-{1}'.format(n, uuid.uuid4()))
    start_date = factory.LazyAttribute(lambda o: timezone.now() - timedelta(days=1))
    end_date = factory.LazyAttribute(lambda o: timezone.now() + timedelta(days=1))

    contact_address = factory.SubFactory(AddressFactory)

    website = factory.Faker('url')
    email = factory.Faker('email')
    phone = factory.Faker('phone_number')
    is_nonprofit = factory.Faker('boolean')
    is_public = factory.Faker('boolean')

    author = factory.SubFactory('base.tests.factories.person.PersonFactory')

    @factory.post_generation
    def tags(obj, create, extracted, **kwargs):
        if create:
            if extracted:
                obj.tags.set(extracted)
            else:
                obj.tags.set([PartnerTagFactory(), PartnerTagFactory()])

    @factory.post_generation
    def entities(obj, create, extracted, **kwargs):
        if create:
            if extracted:
                obj.entities.set(extracted)
            else:
                obj.entities.set([PartnerEntityFactory(partner=obj, author=obj.author)])


class PartnerEntityFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnerEntity

    partner = factory.SubFactory(PartnerFactory)
    name = factory.Sequence(lambda n: 'PartnerEntity-é-{0}'.format(n))
    author = factory.SubFactory('base.tests.factories.person.PersonFactory')
    address = factory.SubFactory(AddressFactory, country=factory.SelfAttribute('..partner.contact_address.country'))
