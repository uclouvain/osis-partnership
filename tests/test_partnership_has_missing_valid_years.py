from django.test import TestCase
from django.urls import reverse

from partnership.models import PartnershipAgreement
from partnership.tests.factories import (
    PartnershipFactory,
    PartnershipYearFactory,
    PartnershipAgreementFactory,
)
from base.tests.factories.academic_year import AcademicYearFactory


class PartnershipHasMissingValidYearsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Years :
        cls.academic_year_15 = AcademicYearFactory(year=2015)
        cls.academic_year_16 = AcademicYearFactory(year=2016)
        cls.academic_year_17 = AcademicYearFactory(year=2017)
        cls.academic_year_18 = AcademicYearFactory(year=2018)
        cls.academic_year_19 = AcademicYearFactory(year=2019)

        # Partnerships :
        cls.partnership_no_agreement = PartnershipFactory()
        cls.partnership_missing_before = PartnershipFactory()
        cls.partnership_missing_after = PartnershipFactory()
        cls.partnership_missing_middle = PartnershipFactory()
        cls.partnership_missing_before_middle_after = PartnershipFactory()
        cls.partnership_full = PartnershipFactory()
        cls.partnership_with_adjacent = PartnershipFactory()
        cls.partnership_with_extra_agreements_before = PartnershipFactory()
        cls.partnership_with_extra_agreements_after = PartnershipFactory()

        # PartnershipYears :
        # No agreement :
        PartnershipYearFactory(
            partnership=cls.partnership_no_agreement,
            academic_year__year = 2015,
        )
        PartnershipYearFactory(
            partnership=cls.partnership_no_agreement,
            academic_year__year = 2019,
        )

        # missing before :
        PartnershipYearFactory(
            partnership=cls.partnership_missing_before,
            academic_year__year = 2015,
        )
        PartnershipYearFactory(
            partnership=cls.partnership_missing_before,
            academic_year__year = 2019,
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_missing_before,
            start_academic_year=cls.academic_year_16,
            end_academic_year=cls.academic_year_19,
            status=PartnershipAgreement.STATUS_VALIDATED,
        )

        # missing after :
        PartnershipYearFactory(
            partnership=cls.partnership_missing_after,
            academic_year__year = 2015,
        )
        PartnershipYearFactory(
            partnership=cls.partnership_missing_after,
            academic_year__year = 2019,
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_missing_after,
            start_academic_year=cls.academic_year_15,
            end_academic_year=cls.academic_year_18,
            status=PartnershipAgreement.STATUS_VALIDATED,
        )

        # missing middle :
        PartnershipYearFactory(
            partnership=cls.partnership_missing_middle,
            academic_year__year = 2015,
        )
        PartnershipYearFactory(
            partnership=cls.partnership_missing_middle,
            academic_year__year = 2019,
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_missing_middle,
            start_academic_year=cls.academic_year_15,
            end_academic_year=cls.academic_year_16,
            status=PartnershipAgreement.STATUS_VALIDATED,
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_missing_middle,
            start_academic_year=cls.academic_year_18,
            end_academic_year=cls.academic_year_19,
            status=PartnershipAgreement.STATUS_VALIDATED,
        )

        # missing before middle after :
        PartnershipYearFactory(
            partnership=cls.partnership_missing_before_middle_after,
            academic_year__year = 2015,
        )
        PartnershipYearFactory(
            partnership=cls.partnership_missing_before_middle_after,
            academic_year__year = 2019,
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_missing_before_middle_after,
            start_academic_year=cls.academic_year_16,
            end_academic_year=cls.academic_year_16,
            status=PartnershipAgreement.STATUS_VALIDATED,
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_missing_before_middle_after,
            start_academic_year=cls.academic_year_18,
            end_academic_year=cls.academic_year_18,
            status=PartnershipAgreement.STATUS_VALIDATED,
        )

        # full :
        PartnershipYearFactory(
            partnership=cls.partnership_full,
            academic_year__year = 2015,
        )
        PartnershipYearFactory(
            partnership=cls.partnership_full,
            academic_year__year = 2019,
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_full,
            start_academic_year=cls.academic_year_15,
            end_academic_year=cls.academic_year_19,
            status=PartnershipAgreement.STATUS_VALIDATED,
        )

        # with adjacent :
        PartnershipYearFactory(
            partnership=cls.partnership_with_adjacent,
            academic_year__year = 2015,
        )
        PartnershipYearFactory(
            partnership=cls.partnership_with_adjacent,
            academic_year__year = 2019,
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_with_adjacent,
            start_academic_year=cls.academic_year_15,
            end_academic_year=cls.academic_year_17,
            status=PartnershipAgreement.STATUS_VALIDATED,
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_with_adjacent,
            start_academic_year=cls.academic_year_18,
            end_academic_year=cls.academic_year_19,
            status=PartnershipAgreement.STATUS_VALIDATED,
        )

        # with extra agreements before :
        PartnershipYearFactory(
            partnership=cls.partnership_with_extra_agreements_before,
            academic_year__year = 2016,
        )
        PartnershipYearFactory(
            partnership=cls.partnership_with_extra_agreements_before,
            academic_year__year = 2019,
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_with_extra_agreements_before,
            start_academic_year=cls.academic_year_15,
            end_academic_year=cls.academic_year_19,
            status=PartnershipAgreement.STATUS_VALIDATED,
        )

    def test_no_agreement(self):
        self.assertTrue(self.partnership_no_agreement.has_missing_valid_years)

    def test_full(self):
        self.assertFalse(self.partnership_full.has_missing_valid_years)

    def test_missing_before(self):
        self.assertTrue(self.partnership_missing_before.has_missing_valid_years)

    def test_missing_after(self):
        self.assertTrue(self.partnership_missing_after.has_missing_valid_years)

    def test_missing_middle(self):
        self.assertTrue(self.partnership_missing_middle.has_missing_valid_years)

    def test_missing_before_middle_after(self):
        self.assertTrue(self.partnership_missing_before_middle_after.has_missing_valid_years)

    def test_with_adjacent(self):
        self.assertFalse(self.partnership_with_adjacent.has_missing_valid_years)

    def test_with_extra_agreements_before(self):
        self.assertFalse(self.partnership_with_extra_agreements_before.has_missing_valid_years)
