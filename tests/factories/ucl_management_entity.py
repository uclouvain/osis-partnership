import factory

from partnership.models import UCLManagementEntity

__all__ = ['UCLManagementEntityFactory']


class UCLManagementEntityFactory(factory.DjangoModelFactory):
    class Meta:
        model = UCLManagementEntity

    entity = factory.SubFactory(
        'base.tests.factories.entity.EntityFactory',
        organization=None,
    )
    academic_responsible = factory.SubFactory(
        'base.tests.factories.person.PersonFactory',
        user=None,
    )
    # Reuse person to speed up tests
    administrative_responsible = factory.SelfAttribute('academic_responsible')
    contact_in_person = factory.SelfAttribute('academic_responsible')
    contact_out_person = factory.SelfAttribute('academic_responsible')
