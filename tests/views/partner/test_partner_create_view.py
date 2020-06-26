from django.test import TestCase
from django.urls import reverse

from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory
from partnership.models import ContactType
from partnership.tests.factories import (
    PartnerTagFactory,
    PartnershipEntityManagerFactory,
)
from reference.tests.factories.country import CountryFactory


class PartnerCreateViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.user_gf = UserFactory()
        PartnershipEntityManagerFactory(person__user=cls.user_gf)

        cls.contact_type = ContactType.objects.create(value='foobar')
        cls.country = CountryFactory()
        cls.data = {
            'organization-name': 'test',
            'organization-start_date': '',
            'organization-end_date': '',
            'organization-code': 'test',
            'partner-is_valid': 'on',
            'partner-pic_code': 'test',
            'partner-erasmus_code': 'test',
            'partner-is_ies': 'True',
            'partner-is_nonprofit': 'True',
            'partner-is_public': 'True',
            'partner-use_egracons': 'on',
            'partner-comment': 'test',
            'partner-phone': 'test',
            'organization-website': 'http://localhost:8000',
            'partner-email': 'test@test.test',
            'partner-tags': [PartnerTagFactory().id],
            'contact_address-name': 'test',
            'contact_address-address': 'test',
            'contact_address-postal_code': 'test',
            'contact_address-city': 'test',
            'contact_address-country': cls.country.pk,
        }

        cls.url = reverse('partnerships:partners:create')
        cls.create_template = 'partnerships/partners/partner_create.html'
        cls.detail_template = 'partnerships/partners/partner_detail.html'

    def test_get_view_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, self.create_template)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, self.create_template)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, self.create_template)

    def test_get_view_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, self.create_template)

    def test_dates_error(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        data['organization-start_date'] = '02/07/2020'
        data['organization-end_date'] = '01/07/2020'
        response = self.client.post(self.url, data, follow=True)
        self.assertIn('start_date', response.context['organization_form'].errors)
        self.assertTemplateNotUsed(response, self.detail_template)

    def test_post(self):
        self.client.force_login(self.user_adri)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertTemplateUsed(response, self.detail_template)
