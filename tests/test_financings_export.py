from django.test import TestCase
from django.urls import reverse
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.user import UserFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person_entity import PersonEntityFactory
from reference.tests.factories.country import CountryFactory
from partnership.tests.factories import FinancingFactory
from partnership.models import Financing


class FinancingsExportViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.country_1 = CountryFactory()
        cls.country_2 = CountryFactory()
        cls.country_3 = CountryFactory()
        cls.academic_year_1 = AcademicYearFactory(year=2040)
        cls.academic_year_2 = AcademicYearFactory()
        cls.academic_year_3 = AcademicYearFactory(year=2041)
        cls.financing_1 = FinancingFactory(academic_year=cls.academic_year_1)
        cls.financing_2 = FinancingFactory(academic_year=cls.academic_year_1)
        cls.financing_3 = FinancingFactory(academic_year=cls.academic_year_3)
        cls.financing_1.countries.set([cls.country_1, cls.country_2])
        cls.financing_2.countries.set([cls.country_3])
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PersonEntityFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.url = reverse('partnerships:financings:export', kwargs={'year': cls.academic_year_1.year})
        cls.url_empty = reverse('partnerships:financings:export', kwargs={'year': cls.academic_year_2.year})

    def test_export_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_export_as_user(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_export_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url, follow=True)
        self.assertEqual(len(response.content.split(b'\n')), 3 + 1)

    def test_export_as_adri_empty(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url_empty, follow=True)
        self.assertEqual(len(response.content.split(b'\n')), 0 + 1)
