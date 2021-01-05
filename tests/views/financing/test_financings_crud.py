from django.shortcuts import resolve_url
from django.test import TestCase

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory
from partnership.models import PartnershipConfiguration
from partnership.tests.factories import (
    PartnershipEntityManagerFactory, FundingSourceFactory, FundingTypeFactory,
)


class FinancingCrudTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.user_adri)

        cls.academic_year = AcademicYearFactory.produce_in_future(quantity=3)[-1]
        PartnershipConfiguration.objects.create(
            partnership_creation_update_min_year=cls.academic_year,
        )

        cls.url = resolve_url('partnerships:financings:list')
        cls.create_url = resolve_url('partnerships:financings:add', model='source')
        source = FundingSourceFactory(name="Bar")
        cls.edit_url = resolve_url(
            'partnerships:financings:edit', model=source, pk=source.pk
        )
        cls.delete_url = resolve_url(
            'partnerships:financings:delete', model=source, pk=source.pk
        )

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

    def test_create_as_user(self):
        self.client.force_login(self.user)
        response = self.client.get(self.create_url, follow=True)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_create_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.create_url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/financings/funding_form.html')

        response = self.client.post(self.create_url, {
            'name': 'Foobar'
        }, follow=True)
        self.assertTemplateUsed(response, 'partnerships/financings/financing_list.html')
        self.assertContains(response, 'Foobar')

    def test_edit_as_user(self):
        self.client.force_login(self.user)
        response = self.client.get(self.edit_url, follow=True)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_edit_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.edit_url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/financings/funding_form.html')

        response = self.client.post(self.edit_url, {
            'name': 'Foobarbaz'
        }, follow=True)
        self.assertTemplateUsed(response, 'partnerships/financings/financing_list.html')
        self.assertContains(response, 'Foobarbaz')

    def test_disable_children(self):
        self.client.force_login(self.user_adri)
        funding_type = FundingTypeFactory()
        program = funding_type.program
        url = resolve_url(
            'partnerships:financings:edit', model=program, pk=program.pk
        )
        response = self.client.post(url, {
            'name': 'Foobarbaz',
            'is_active': False,
            'source': program.source_id,
        }, follow=True)
        self.assertTemplateUsed(response, 'partnerships/financings/financing_list.html')
        self.assertContains(response, 'Foobarbaz')

        funding_type.refresh_from_db()
        self.assertFalse(funding_type.is_active)

    def test_delete_as_user(self):
        self.client.force_login(self.user)
        response = self.client.get(self.delete_url, follow=True)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_delete_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.delete_url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/financings/funding_delete.html')

        response = self.client.post(self.delete_url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/financings/financing_list.html')
        self.assertNotContains(response, 'Bar')
