from django.test import TestCase

from base.tests.factories.academic_year import AcademicYearFactory, get_current_year
from base.tests.factories.entity import EntityWithVersionFactory
from partnership.models import AgreementStatus
from partnership.tests.factories import (
    PartnershipAgreementFactory as BasePartnershipAgreementFactory,
    PartnershipFactory as BasePartnershipFactory,
    PartnershipYearFactory, PartnerFactory, MediaFactory,
)


class PartnershipHasMissingValidYearsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Performance fix: don't bother recreating linked objects
        class PartnershipFactory(BasePartnershipFactory):
            partner = PartnerFactory()
            ucl_entity = EntityWithVersionFactory(organization=None)

        class PartnershipAgreementFactory(BasePartnershipAgreementFactory):
            media = MediaFactory()

        # Years :
        current_year = get_current_year()
        cls.academic_year_less_3 = AcademicYearFactory(year=current_year - 3)
        cls.academic_year_less_2 = AcademicYearFactory(year=current_year - 2)
        cls.academic_year_less_1 = AcademicYearFactory(year=current_year - 1)
        cls.current_academic_year = AcademicYearFactory(year=current_year)
        cls.academic_year_more_1 = AcademicYearFactory(year=current_year + 1)

        # Partnerships :
        cls.partnership_no_agreement = PartnershipFactory(
            years__academic_year=cls.academic_year_less_3
        )
        cls.partnership_missing_before = PartnershipFactory(years=[])
        cls.partnership_missing_after = PartnershipFactory(years=[])
        cls.partnership_missing_middle = PartnershipFactory(years=[])
        cls.partnership_missing_before_middle_after = PartnershipFactory(
            years=[],
        )
        cls.partnership_full = PartnershipFactory(years=[])
        cls.partnership_no_years = PartnershipFactory(years=[])
        cls.partnership_with_adjacent = PartnershipFactory(years=[])
        cls.partnership_with_extra_agreements_before = PartnershipFactory(
            years=[],
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
        self.assertIsNone(self.partnership_no_agreement.valid_start_date)
        self.assertIsNone(self.partnership_no_agreement.valid_end_date)

    def test_full(self):
        self.assertFalse(self.partnership_full.has_missing_valid_years)
        self.assertEqual(self.partnership_full.valid_start_date,
                         self.academic_year_less_3.start_date)
        self.assertEqual(self.partnership_full.valid_end_date,
                         self.academic_year_more_1.end_date)

    def test_no_years(self):
        self.assertFalse(self.partnership_no_years.has_missing_valid_years)

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
