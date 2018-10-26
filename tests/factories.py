import uuid
from datetime import timedelta

import factory
from django.utils import timezone

from base.tests.factories.academic_year import get_current_year
from partnership.models import (Address, Contact, ContactType, Media, Partner,
                                PartnerEntity, Partnership,
                                PartnershipAgreement, PartnershipTag,
                                PartnershipYear, PartnershipYearEducationField,
                                PartnershipYearEducationLevel, PartnerTag,
                                PartnerType, UCLManagementEntity,
                                PartnershipEntityManager, Financing)


class PartnershipEntityManagerFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnershipEntityManager

    person = factory.SubFactory('base.tests.factories.person.PersonFactory')
    entity = factory.SubFactory('base.tests.factories.entity.EntityFactory')


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
    address = factory.SubFactory(AddressFactory, country=factory.SelfAttribute('..partner.contact_address.country'))


class PartnershipTagFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnershipTag

    value = factory.Sequence(lambda n: 'PartnershipTag-é-{0}'.format(n))


class PartnershipFactory(factory.DjangoModelFactory):
    class Meta:
        model = Partnership

    partner = factory.SubFactory(PartnerFactory)
    partner_entity = factory.SubFactory(PartnerEntityFactory, partner=factory.SelfAttribute('..partner'))

    ucl_university = factory.SubFactory(
        'base.tests.factories.entity.EntityFactory',
        country=factory.SelfAttribute('..partner.contact_address.country'),
    )

    author = factory.SubFactory('base.tests.factories.user.UserFactory')

    @factory.post_generation
    def tags(obj, create, extracted, **kwargs):
        if create:
            if extracted:
                obj.tags = extracted
            else:
                obj.tags = [PartnershipTagFactory(), PartnershipTagFactory()]

    @factory.post_generation
    def contacts(obj, create, extracted, **kwargs):
        if create:
            if extracted:
                obj.contacts = extracted
            else:
                obj.contacts = [ContactFactory(), ContactFactory()]

    @factory.post_generation
    def years(obj, create, extracted, **kwargs):
        if create:
            if extracted is not None:
                obj.years = extracted
            else:
                obj.years = [PartnershipYearFactory(partnership=obj)]


class PartnershipYearEducationFieldFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnershipYearEducationField

    code = factory.Sequence(lambda n: 'code-é-{0}'.format(n))
    label = factory.Faker('word')


class PartnershipYearEducationLevelFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnershipYearEducationLevel

    code = factory.Sequence(lambda n: 'code-é-{0}'.format(n))
    label = factory.Faker('word')


class PartnershipYearFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnershipYear

    partnership_type = 'mobility'
    academic_year = factory.SubFactory('base.tests.factories.academic_year.AcademicYearFactory', year=get_current_year())
    partnership = factory.SubFactory('partnership.tests.factories.PartnershipFactory')


class PartnershipAgreementFactory(factory.DjangoModelFactory):
    class Meta:
        model = PartnershipAgreement

    partnership = factory.SubFactory(PartnershipFactory)
    start_academic_year = factory.SubFactory('base.tests.factories.academic_year.AcademicYearFactory')
    end_academic_year = factory.SubFactory('base.tests.factories.academic_year.AcademicYearFactory')
    media = factory.SubFactory('partnership.tests.factories.MediaFactory')


class MediaFactory(factory.DjangoModelFactory):
    class Meta:
        model = Media

    name = factory.Faker('word')
    description = factory.Faker('sentence')
    url = factory.Faker('url')
    visibility = Media.VISIBILITY_PUBLIC
    author = factory.SubFactory('base.tests.factories.user.UserFactory')


class ContactTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = ContactType

    value = factory.Sequence(lambda n: 'ContactType-{0}'.format(n))


class ContactFactory(factory.DjangoModelFactory):
    class Meta:
        model = Contact

    type = factory.SubFactory(ContactTypeFactory)
    title = Contact.TITLE_MISTER


class UCLManagementEntityFactory(factory.DjangoModelFactory):
    class Meta:
        model = UCLManagementEntity

    faculty = factory.SubFactory(
        'base.tests.factories.entity.EntityFactory',
    )
    entity = factory.SubFactory(
        'base.tests.factories.entity.EntityFactory',
    )
    academic_responsible = factory.SubFactory(
        'base.tests.factories.person.PersonFactory',
    )
    administrative_responsible = factory.SubFactory(
        'base.tests.factories.person.PersonFactory'
    )
    contact_in_person = factory.SubFactory(
        'base.tests.factories.person.PersonFactory',
    )
    contact_out_person = factory.SubFactory(
        'base.tests.factories.person.PersonFactory',
    )


class FinancingFactory(factory.DjangoModelFactory):
    class Meta:
        model = Financing
