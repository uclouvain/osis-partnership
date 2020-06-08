import factory

from partnership.models import Media, MediaVisibility

__all__ = ['MediaFactory']


class MediaFactory(factory.DjangoModelFactory):
    class Meta:
        model = Media

    name = factory.Faker('word')
    description = factory.Faker('sentence')
    url = factory.Faker('url')
    visibility = MediaVisibility.PUBLIC.name
