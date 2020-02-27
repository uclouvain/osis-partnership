import factory

from partnership.models import Financing

__all__ = ['FinancingFactory']


class FinancingFactory(factory.DjangoModelFactory):
    class Meta:
        model = Financing

    name = factory.Faker('word')
    url = factory.Faker('url')
