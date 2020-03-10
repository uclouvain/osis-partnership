from django.test import TestCase

from base.tests.factories.academic_year import AcademicYearFactory, get_current_year
from partnership.models import AgreementStatus
from partnership.tests.factories import (
    PartnershipAgreementFactory,
    PartnershipFactory,
    PartnershipYearFactory
)


class PartnershipHasMissingValidYearsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Years :
        current_year = get_current_year()
        cls.academic_year_less_3 = AcademicYearFactory(year=current_year - 3)
        cls.academic_year_less_2 = AcademicYearFactory(year=current_year - 2)
        cls.academic_year_less_1 = AcademicYearFactory(year=current_year - 1)
        cls.current_academic_year = AcademicYearFactory(year=current_year)
        cls.academic_year_more_1 = AcademicYearFactory(year=current_year + 1)

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
            academic_year=cls.academic_year_less_3,
        )
        PartnershipYearFactory(
            partnership=cls.partnership_no_agreement,
            academic_year=cls.academic_year_more_1,
        )

        # missing before :
        PartnershipYearFactory(
            partnership=cls.partnership_missing_before,
            academic_year=cls.academic_year_less_3,
        )
        PartnershipYearFactory(
            partnership=cls.partnership_missing_before,
            academic_year=cls.academic_year_more_1,
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_missing_before,
            start_academic_year=cls.academic_year_less_2,
            end_academic_year=cls.academic_year_more_1,
            status=AgreementStatus.VALIDATED.name,
        )

        # missing after :
        PartnershipYearFactory(
            partnership=cls.partnership_missing_after,
            academic_year=cls.academic_year_less_3,
        )
        PartnershipYearFactory(
            partnership=cls.partnership_missing_after,
            academic_year=cls.academic_year_more_1,
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_missing_after,
            start_academic_year=cls.academic_year_less_3,
            end_academic_year=cls.current_academic_year,
            status=AgreementStatus.VALIDATED.name,
        )

        # missing middle :
        PartnershipYearFactory(
            partnership=cls.partnership_missing_middle,
            academic_year=cls.academic_year_less_3,
        )
        PartnershipYearFactory(
            partnership=cls.partnership_missing_middle,
            academic_year=cls.academic_year_more_1,
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_missing_middle,
            start_academic_year=cls.academic_year_less_3,
            end_academic_year=cls.academic_year_less_2,
            status=AgreementStatus.VALIDATED.name,
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_missing_middle,
            start_academic_year=cls.current_academic_year,
            end_academic_year=cls.academic_year_more_1,
            status=AgreementStatus.VALIDATED.name,
        )

        # missing before middle after :
        PartnershipYearFactory(
            partnership=cls.partnership_missing_before_middle_after,
            academic_year=cls.academic_year_less_3,
        )
        PartnershipYearFactory(
            partnership=cls.partnership_missing_before_middle_after,
            academic_year=cls.academic_year_more_1,
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_missing_before_middle_after,
            start_academic_year=cls.academic_year_less_2,
            end_academic_year=cls.academic_year_less_2,
            status=AgreementStatus.VALIDATED.name,
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_missing_before_middle_after,
            start_academic_year=cls.current_academic_year,
            end_academic_year=cls.current_academic_year,
            status=AgreementStatus.VALIDATED.name,
        )

        # full :
        PartnershipYearFactory(
            partnership=cls.partnership_full,
            academic_year=cls.academic_year_less_3,
        )
        PartnershipYearFactory(
            partnership=cls.partnership_full,
            academic_year=cls.academic_year_more_1,
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_full,
            start_academic_year=cls.academic_year_less_3,
            end_academic_year=cls.academic_year_more_1,
            status=AgreementStatus.VALIDATED.name,
        )

        # with adjacent :
        PartnershipYearFactory(
            partnership=cls.partnership_with_adjacent,
            academic_year=cls.academic_year_less_3,
        )
        PartnershipYearFactory(
            partnership=cls.partnership_with_adjacent,
            academic_year=cls.academic_year_more_1,
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_with_adjacent,
            start_academic_year=cls.academic_year_less_3,
            end_academic_year=cls.academic_year_less_1,
            status=AgreementStatus.VALIDATED.name,
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_with_adjacent,
            start_academic_year=cls.current_academic_year,
            end_academic_year=cls.academic_year_more_1,
            status=AgreementStatus.VALIDATED.name,
        )

        # with extra agreements before :
        PartnershipYearFactory(
            partnership=cls.partnership_with_extra_agreements_before,
            academic_year=cls.academic_year_less_2,
        )
        PartnershipYearFactory(
            partnership=cls.partnership_with_extra_agreements_before,
            academic_year=cls.academic_year_more_1,
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_with_extra_agreements_before,
            start_academic_year=cls.academic_year_less_3,
            end_academic_year=cls.academic_year_more_1,
            status=AgreementStatus.VALIDATED.name,
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