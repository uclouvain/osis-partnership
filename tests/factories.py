from datetime import timedelta

import factory
from django.utils import timezone

from partnership.models import PartnerType, PartnerTag, Partner, Partnership, PartnershipTag, PartnershipType, \
    PartnerEntity, Media


class PartnerTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnerType

    value = factory.Sequence(lambda n: 'PartnerType-é-{0}'.format(n))


class PartnerTagFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnerTag

    value = factory.Sequence(lambda n: 'PartnerTag-é-{0}'.format(n))


class PartnerFactory(factory.DjangoModelFactory):
    class Meta:
        model = Partner

    is_valid = True
    name = factory.Sequence(lambda n: 'Partner-é-{0}'.format(n))
    is_ies = factory.Faker('boolean')
    partner_type = factory.SubFactory(PartnerTypeFactory)
    partner_code = factory.Sequence(lambda n: 'partner_code-é-{0}'.format(n))
    pic_code = factory.Sequence(lambda n: 'pic_code-é-{0}'.format(n))
    erasmus_code = factory.Sequence(lambda n: 'erasmus_code-é-{0}'.format(n))
    start_date = factory.LazyAttribute(lambda o: timezone.now() - timedelta(days=1))
    end_date = factory.LazyAttribute(lambda o: timezone.now() + timedelta(days=1))

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


class PartnershipTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnershipType

    value = factory.Sequence(lambda n: 'PartnershipType-é-{0}'.format(n))


class PartnershipTagFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnershipTag

    value = factory.Sequence(lambda n: 'PartnershipTag-é-{0}'.format(n))


class PartnershipFactory(factory.DjangoModelFactory):
    class Meta:
        model = Partnership

    is_valid = True
    partner = factory.SubFactory(PartnerFactory)
    start_date = factory.LazyAttribute(lambda o: timezone.now() - timedelta(days=1))
    end_date = factory.LazyAttribute(lambda o: timezone.now() + timedelta(days=1))

    mobility_type = factory.Faker('random_element', elements=dict(Partnership.MOBILITY_TYPE_CHOICES).keys())
    partnership_type = factory.SubFactory(PartnershipTypeFactory)

    partner_entity = factory.SubFactory(PartnerEntityFactory)
    ucl_university = factory.SubFactory('base.tests.factories.entity_version.EntityVersionFactory')

    author = factory.SubFactory('base.tests.factories.user.UserFactory')

    @factory.post_generation
    def tags(obj, create, extracted, **kwargs):
        if create:
            if extracted:
                obj.tags = extracted
            else:
                obj.tags = [PartnershipTagFactory(), PartnershipTagFactory()]


class MediaFactory(factory.DjangoModelFactory):
    class Meta:
        model = Media

    name = factory.Faker('word')
    description = factory.Faker('sentence')
    url = factory.Faker('url')
    visibility = Media.VISIBILITY_PUBLIC
    author = factory.SubFactory('base.tests.factories.user.UserFactory')
