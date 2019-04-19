from django.test import TestCase
from django.urls import reverse

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.person import PersonFactory
from partnership.tests.factories import PartnershipFactory, PartnerFactory, UCLManagementEntityFactory
from reference.models.continent import Continent
from reference.tests.factories.country import CountryFactory


class ConfigurationApiViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('partnerships_api_v1:configuration')

        AcademicYearFactory.produce_in_future(quantity=3)

        cls.supervisor_partnership = PersonFactory()
        cls.supervisor_management_entity = PersonFactory()

        PartnerFactory()
        PartnershipFactory(supervisor=cls.supervisor_partnership)
        partnership = PartnershipFactory()
        PartnershipFactory()

        UCLManagementEntityFactory(
            faculty=partnership.ucl_university,
            academic_responsible=cls.supervisor_management_entity
        )

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

    def test_ucl_universities(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_supervisors(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_education_fields(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_fundings(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
