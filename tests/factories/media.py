import factory

from partnership.models import Media

__all__ = ['MediaFactory']


class MediaFactory(factory.DjangoModelFactory):
    class Meta:
        model = Media

    name = factory.Faker('word')
    description = factory.Faker('sentence')
    url = factory.Faker('url')
    visibility = Media.VISIBILITY_PUBLIC
    author = factory.SubFactory('base.tests.factories.person.PersonFactory')
