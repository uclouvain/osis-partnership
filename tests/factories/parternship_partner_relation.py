import factory

from partnership.models import PartnershipPartnerRelation
from . import PartnershipFactory


class PartnershipPartnerRelationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PartnershipPartnerRelation

    partnership = factory.SubFactory(PartnershipFactory)
    entity = factory.SubFactory(
        'base.tests.factories.entity.EntityWithVersionFactory',
        version__acronym="SO"
    )
