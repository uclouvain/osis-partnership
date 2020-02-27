import factory

from partnership.models import ContactType, Contact

__all__ = [
    'ContactFactory',
    'ContactTypeFactory',
]


class ContactTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = ContactType

    value = factory.Sequence(lambda n: 'ContactType-{0}'.format(n))


class ContactFactory(factory.DjangoModelFactory):
    class Meta:
        model = Contact

    type = factory.SubFactory(ContactTypeFactory)
    title = Contact.TITLE_MISTER
