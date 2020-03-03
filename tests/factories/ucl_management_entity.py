import factory

from partnership.models import UCLManagementEntity

__all__ = ['UCLManagementEntityFactory']


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
