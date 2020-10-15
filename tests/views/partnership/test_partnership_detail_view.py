from django.test import TestCase
from django.urls import reverse

from base.tests.factories.academic_year import AcademicYearFactory
from partnership.tests.factories import (
    PartnershipEntityManagerFactory,
    PartnershipFactory,
    PartnershipYearFactory,
    FinancingFactory,
)
from reference.tests.factories.country import CountryFactory


class PartnershipDetailViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.partnership = PartnershipFactory()
        cls.user = PartnershipEntityManagerFactory().person.user
        cls.url = reverse('partnerships:detail', kwargs={'pk': cls.partnership.pk})

    def test_get_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnership/partnership_detail.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')

    def test_get_financing(self):
        self.client.force_login(self.user)

        academic_year = AcademicYearFactory()
        year = PartnershipYearFactory(
            partnership__partner__contact_address=None,
            academic_year=academic_year,
        )

        # No financing because no address
        self.assertEqual(year.get_financing(), None)

        year = PartnershipYearFactory(
            partnership__partner__contact_address__country__iso_code="FO",
            academic_year=academic_year,
        )

        # No financing for this country
        self.assertEqual(year.get_financing(), None)

        financing = FinancingFactory(academic_year=academic_year)
        country = CountryFactory(iso_code="FO")
        financing.countries.add(country)

        # Correct financing
        self.assertEqual(year.get_financing(), financing)
