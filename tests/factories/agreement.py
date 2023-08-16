import factory

from partnership.models import PartnershipAgreement
from partnership.tests.factories.partnership import PartnershipFactory

__all__ = ['PartnershipAgreementFactory']


class PartnershipAgreementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PartnershipAgreement

    partnership = factory.SubFactory(PartnershipFactory)
    start_academic_year = factory.SubFactory('base.tests.factories.academic_year.AcademicYearFactory')
    end_academic_year = factory.SubFactory('base.tests.factories.academic_year.AcademicYearFactory')
    media = factory.SubFactory('partnership.tests.factories.MediaFactory')
