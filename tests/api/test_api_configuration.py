from django.test import TestCase
from django.urls import reverse

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.person import PersonFactory
from partnership.models import PartnershipConfiguration
from partnership.tests.factories import PartnershipFactory, PartnerFactory, UCLManagementEntityFactory, \
    PartnershipYearFactory, PartnershipAgreementFactory, PartnershipYearEducationFieldFactory, FinancingFactory
from reference.models.continent import Continent
from reference.tests.factories.country import CountryFactory


class ConfigurationApiViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('partnership_api_v1:configuration')

        AcademicYearFactory.produce_in_future(quantity=3)
        current_academic_year = PartnershipConfiguration.get_configuration().get_current_academic_year_for_api()

        # Partnerships
        cls.supervisor_partnership = PersonFactory()
        cls.supervisor_management_entity = PersonFactory()

        partnership = PartnershipFactory(supervisor=cls.supervisor_partnership, years=[])
        year = PartnershipYearFactory(
            partnership=partnership,
            academic_year=current_academic_year,
        )
        year.education_fields.add(PartnershipYearEducationFieldFactory())
        PartnershipAgreementFactory(
            partnership=partnership,
            start_academic_year=current_academic_year,
            end_academic_year__year=current_academic_year.year + 1,
        )

        partnership = PartnershipFactory(years=[])
        PartnershipYearFactory(partnership=partnership, academic_year=current_academic_year)
        PartnershipAgreementFactory(
            partnership=partnership,
            start_academic_year=current_academic_year,
            end_academic_year__year=current_academic_year.year + 1,
        )
        UCLManagementEntityFactory(
            entity=partnership.ucl_university,
            academic_responsible=cls.supervisor_management_entity
        )
        financing = FinancingFactory(academic_year=current_academic_year)
        financing.countries.add(partnership.partner.contact_address.country)

        # Some noises
        PartnerFactory()
        PartnershipFactory()

        # Continents
        continent = Continent.objects.create(code='AA', name='aaaaa')
        CountryFactory(continent=continent)
        CountryFactory(continent=continent)
        CountryFactory()

    def test_continents(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('continents', data)
        self.assertEqual(len(data['continents']), 1)
        self.assertEqual(len(data['continents'][0]['countries']), 2)

    def test_partners(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('partners', data)
        self.assertEqual(len(data['partners']), 2)

    def test_ucl_universities(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('ucl_universities', data)
        self.assertEqual(len(data['ucl_universities']), 2)

    def test_supervisors(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('supervisors', data)
        self.assertEqual(len(data['supervisors']), 2)

    def test_education_fields(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('education_fields', data)
        self.assertEqual(len(data['education_fields']), 1)

    def test_fundings(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('fundings', data)
        self.assertEqual(len(data['fundings']), 1)
