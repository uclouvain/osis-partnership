import factory

from partnership.models import Contact, ContactTitle, ContactType

__all__ = [
    'ContactFactory',
    'ContactTypeFactory',
]


class ContactTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ContactType

    value = factory.Sequence(lambda n: 'ContactType-{0}'.format(n))


class ContactFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Contact

    title = ContactTitle.MISTER.name
