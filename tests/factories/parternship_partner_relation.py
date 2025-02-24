import factory

from partnership.models import PartnershipPartnerRelation, PartnershipProductionSupplement, PartnershipDiplomaWithUCL
from . import PartnershipFactory


class PartnershipPartnerRelationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PartnershipPartnerRelation

    partnership = factory.SubFactory(PartnershipFactory)
    entity = factory.SubFactory(
        'base.tests.factories.entity.EntityWithVersionFactory',
        version__acronym="SO"
    )


class PartnerEntityRelationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PartnershipPartnerRelation

    partnership = factory.SubFactory(PartnershipFactory)
    entity = factory.SubFactory(
        'base.tests.factories.entity.EntityWithVersionFactory',
        version__acronym="SO"
    )
    diploma_with_ucl_by_partner = factory.fuzzy.FuzzyChoice(PartnershipDiplomaWithUCL.choices())
    diploma_prod_by_partner = factory.fuzzy.FuzzyChoice((False, True))
    supplement_prod_by_partner = factory.fuzzy.FuzzyChoice(PartnershipProductionSupplement.choices())
