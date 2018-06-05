from datetime import timedelta

import factory
from django.utils import timezone

from partnerships.models import PartnerType, PartnerTag, Partner, Partnership


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


class PartnershipTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnerType

    value = factory.Sequence(lambda n: 'PartnershipType-é-{0}'.format(n))


class PartnershipTagFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnerTag

    value = factory.Sequence(lambda n: 'PartnershipTag-é-{0}'.format(n))


class PartnershipsFactory(factory.DjangoModelFactory):
    class Meta:
        model = Partnership

    is_valid = True
    partner = factory.SubFactory(Partner)
    start_date = factory.LazyAttribute(lambda o: timezone.now() - timedelta(days=1))
    end_date = factory.LazyAttribute(lambda o: timezone.now() + timedelta(days=1))

    mobility_type = factory.Faker('random_element', elements=dict(Partnership.MOBILITY_TYPE_CHOICES).keys())
    partner_type = factory.SubFactory(PartnershipTypeFactory)

    author = factory.SubFactory('base.tests.factories.user.UserFactory')

    @factory.post_generation
    def tags(obj, create, extracted, **kwargs):
        if create:
            if extracted:
                obj.tags = extracted
            else:
                obj.tags = [PartnershipTagFactory(), PartnershipTagFactory()]
