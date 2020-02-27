import factory

from partnership.models import Address

__all__ = ['AddressFactory']


class AddressFactory(factory.DjangoModelFactory):
    class Meta:
        model = Address

    name = factory.Faker('name')
    address = factory.Faker('street_name')
    postal_code = factory.Faker('zipcode')
    city = factory.Faker('city')
    country = factory.SubFactory('reference.tests.factories.country.CountryFactory')
