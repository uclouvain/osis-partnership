from django.test import TestCase
from django.urls import reverse

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory
from partnership.models import Financing
from partnership.tests.factories import (FinancingFactory,
                                         PartnershipEntityManagerFactory)
from reference.models.country import Country
from reference.tests.factories.country import CountryFactory


class FinancingsExportViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.country_1 = CountryFactory(name="country_1", iso_code="C1")
        cls.country_2 = CountryFactory(name="country_2", iso_code="C2")
        cls.country_3 = CountryFactory(name="country_3", iso_code="C3")
        cls.academic_year_1 = AcademicYearFactory(year=2040)
        cls.academic_year_2 = AcademicYearFactory()
        cls.academic_year_3 = AcademicYearFactory(year=2041)
        cls.financing_1 = FinancingFactory(name="financing_1", academic_year=cls.academic_year_1)
        cls.financing_2 = FinancingFactory(name="financing_2", academic_year=cls.academic_year_1)
        cls.financing_3 = FinancingFactory(name="financing_3", academic_year=cls.academic_year_3)
        cls.financing_1.countries.set([cls.country_1, cls.country_2])
        cls.financing_2.countries.set([cls.country_3])
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.user_adri)
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
        self.assertEqual(len(response.content.split(b'\n')), Country.objects.count() + 1 + 1)
        self.assertEqual(response.content.count(b'financing_1'), 2)
        self.assertEqual(response.content.count(b'financing_2'), 1)
        self.assertEqual(response.content.count(b'financing_3'), 0)

    def test_export_as_adri_empty(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url_empty, follow=True)
        self.assertEqual(len(response.content.split(b'\n')), Country.objects.count() + 1 + 1)
        self.assertEqual(response.content.count(b'financing_1'), 0)
        self.assertEqual(response.content.count(b'financing_2'), 0)
        self.assertEqual(response.content.count(b'financing_3'), 0)
