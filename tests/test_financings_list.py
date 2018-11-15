from django.test import TestCase
from django.urls import reverse

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory
from partnership.tests.factories import (FinancingFactory,
                                         PartnershipEntityManagerFactory)
from reference.models.country import Country
from reference.tests.factories.country import CountryFactory


class FinancingsListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        for i in range(50):
            CountryFactory()
        cls.selected_countries_1 = Country.objects.all()[:20]
        cls.selected_countries_2 = Country.objects.all()[20:30]
        cls.academic_year_1 = AcademicYearFactory()
        cls.academic_year_2 = AcademicYearFactory()
        cls.financing_1 = FinancingFactory(academic_year=cls.academic_year_1)
        cls.financing_1.countries.set(cls.selected_countries_1)
        cls.financing_2 = FinancingFactory(academic_year=cls.academic_year_2)
        cls.financing_2.countries.set(cls.selected_countries_2)

        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.url = reverse('partnerships:financings:list', kwargs={'year': cls.academic_year_1.year})

    def test_list_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/financings/financing_list.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_list_as_user(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/financings/financing_list.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_list_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/financings/financing_list.html')
