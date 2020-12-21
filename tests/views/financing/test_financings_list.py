from django.shortcuts import resolve_url
from django.test import tag

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory
from partnership.models import PartnershipConfiguration
from partnership.tests import TestCase
from partnership.tests.factories import (
    FinancingFactory,
    PartnershipEntityManagerFactory,
)
from reference.models.country import Country
from reference.tests.factories.country import CountryFactory


class FinancingListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        for i in range(50):
            CountryFactory()
        cls.selected_countries_1 = Country.objects.all()[:20]
        cls.selected_countries_2 = Country.objects.all()[20:30]
        cls.academic_year_1 = AcademicYearFactory.produce_in_future(quantity=3)[-1]
        cls.academic_year_2 = AcademicYearFactory()
        PartnershipConfiguration.objects.create(
            partnership_creation_update_min_year=cls.academic_year_1,
        )
        cls.financing_1 = FinancingFactory(academic_year=cls.academic_year_1)
        cls.financing_1.countries.set(cls.selected_countries_1)
        cls.financing_2 = FinancingFactory(academic_year=cls.academic_year_2)
        cls.financing_2.countries.set(cls.selected_countries_2)

        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.user_adri)

        cls.url = resolve_url('partnerships:financings:list', year=cls.academic_year_1.year)
        cls.default_url = resolve_url('partnerships:financings:list')

    def test_list_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/financings/financing_list.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_list_as_user(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/financings/financing_list.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_list_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/financings/financing_list.html')

        response = self.client.get(self.default_url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/financings/financing_list.html')

        # Post to list should redirect
        response = self.client.post(self.url, {
            'year': self.academic_year_2.pk,
        })
        self.assertRedirects(
            response,
            resolve_url('partnerships:financings:list', year=self.academic_year_2.year),
        )

        # Except when sending no data
        response = self.client.post(self.url)
        self.assertFalse(response.context['form'].is_valid())

        # And post empty should redirect to current year for creation/modification
        response = self.client.post(self.url, {'year': ''})
        self.assertRedirects(response, self.url)

    @tag('perf')
    def test_queries_count(self):
        self.client.force_login(self.user_adri)
        with self.assertNumQueriesLessThan(27):
            self.client.get(self.default_url)

        with self.assertNumQueriesLessThan(12):
            self.client.get(self.default_url, HTTP_ACCEPT='application/json')
