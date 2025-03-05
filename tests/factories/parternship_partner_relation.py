import factory

from base.tests.factories.academic_year import AcademicYearFactory
from partnership.models import PartnershipPartnerRelation, PartnershipProductionSupplement, PartnershipDiplomaWithUCL
from . import PartnershipFactory
from ...models.relation_year import PartnershipPartnerRelationYear


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


class PartnershipPartnerRelationYearFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PartnershipPartnerRelationYear

    partnership_relation = factory.SubFactory(PartnershipPartnerRelationFactory)
    academic_year = factory.SubFactory(AcademicYearFactory)
    type_diploma_by_partner = factory.Iterator([choice[0] for choice in PartnershipDiplomaWithUCL.choices()])
    diploma_prod_by_partner = factory.Faker('boolean')
    supplement_prod_by_partner = factory.Iterator([choice[0] for choice in PartnershipProductionSupplement.choices()])
    partner_referent = factory.Faker('boolean')
