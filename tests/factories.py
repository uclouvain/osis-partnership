from datetime import timedelta

import factory
from django.utils import timezone
import uuid
from partnership.models import PartnerType, PartnerTag, Partner, Partnership, PartnershipTag, PartnershipType, \
    PartnerEntity, Media, Address, PartnershipYear, PartnershipAgreement


class PartnerTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnerType
        django_get_or_create = ('value',)

    value = factory.Sequence(lambda n: 'PartnerType-{0}'.format(n))


class PartnerTagFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnerTag
        django_get_or_create=('value',)

    value = factory.Sequence(lambda n: 'PartnerTag-é-{0}-{1}'.format(n, uuid.uuid4()))


class AddressFactory(factory.DjangoModelFactory):
    class Meta:
        model = Address

    name = factory.Faker('name')
    address = factory.Faker('street_name')
    postal_code = factory.Faker('zipcode')
    city = factory.Faker('city')
    country = factory.SubFactory('reference.tests.factories.country.CountryFactory')


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

    author = factory.SubFactory('base.tests.factories.user.UserFactory')

    @factory.post_generation
    def tags(obj, create, extracted, **kwargs):
        if create:
            if extracted:
                obj.tags = extracted
            else:
                obj.tags = [PartnerTagFactory(), PartnerTagFactory()]

    @factory.post_generation
    def entities(obj, create, extracted, **kwargs):
        if create:
            if extracted:
                obj.entities = extracted
            else:
                obj.entities = [PartnerEntityFactory(partner=obj, author=obj.author)]


class PartnerEntityFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnerEntity

    partner = factory.SubFactory(PartnerFactory)
    name = factory.Sequence(lambda n: 'PartnerEntity-é-{0}'.format(n))
    author = factory.SubFactory('base.tests.factories.user.UserFactory')
    address = factory.SubFactory(AddressFactory)


class PartnershipTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnershipType

    value = factory.Sequence(lambda n: 'PartnershipType-é-{0}-{1}'.format(n, uuid.uuid4()))


class PartnershipTagFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnershipTag

    value = factory.Sequence(lambda n: 'PartnershipTag-é-{0}'.format(n))


class PartnershipFactory(factory.DjangoModelFactory):
    class Meta:
        model = Partnership
        django_get_or_create = ('tags', 'partner')

    is_valid = True
    partner = factory.SubFactory(PartnerFactory)
    start_date = factory.LazyAttribute(lambda o: timezone.now() - timedelta(days=1))
    end_date = factory.LazyAttribute(lambda o: timezone.now() + timedelta(days=1))

    partner_entity = factory.SubFactory(PartnerEntityFactory)
    ucl_university = factory.SubFactory('base.tests.factories.entity.EntityFactory')

    author = factory.SubFactory('base.tests.factories.user.UserFactory')

    @factory.post_generation
    def tags(obj, create, extracted, **kwargs):
        if create:
            if extracted:
                obj.tags = extracted
            else:
                obj.tags = [PartnershipTagFactory(), PartnershipTagFactory()]


class PartnershipYearFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnershipYear

    mobility_type = factory.Faker('random_element', elements=dict(PartnershipYear.MOBILITY_TYPE_CHOICES).keys())
    partnership_type = factory.SubFactory(PartnershipTypeFactory)


class PartnershipOfferFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnershipAgreement

    media = factory.SubFactory('partnership.tests.factories.MediaFactory')


class MediaFactory(factory.DjangoModelFactory):
    class Meta:
        model = Media

    name = factory.Faker('word')
    description = factory.Faker('sentence')
    url = factory.Faker('url')
    visibility = Media.VISIBILITY_PUBLIC
    author = factory.SubFactory('base.tests.factories.user.UserFactory')
