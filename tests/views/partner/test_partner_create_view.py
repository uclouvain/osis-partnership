from django.core import mail
from django.test import TestCase
from django.urls import reverse

from base.models.enums.organization_type import ACADEMIC_PARTNER
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
            'organization-start_date': '02/07/2020',
            'organization-end_date': '',
            'organization-code': 'test',
            'organization-type': ACADEMIC_PARTNER,
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
            'contact_address-street': 'test',
            'contact_address-postal_code': 'test',
            'contact_address-city': 'test',
            'contact_address-country': cls.country.pk,
            'contact_address-location_0': -30,
            'contact_address-location_1': 20,
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
        data['organization-end_date'] = '01/07/2020'
        response = self.client.post(self.url, data, follow=True)
        self.assertIn('start_date', response.context['organization_form'].errors)
        self.assertTemplateNotUsed(response, self.detail_template)

    def test_ies_pic_requirements(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        data['partner-is_ies'] = 'False'
        data['partner-pic_code'] = ''
        data['partner-is_nonprofit'] = ''
        data['partner-is_public'] = ''
        data['partner-email'] = ''
        data['partner-phone'] = ''
        response = self.client.post(self.url, data, follow=True)
        self.assertIn('is_nonprofit', response.context_data['form'].errors)
        self.assertIn('is_public', response.context_data['form'].errors)
        self.assertIn('email', response.context_data['form'].errors)
        self.assertIn('phone', response.context_data['form'].errors)
        self.assertIn('contact_type', response.context_data['form'].errors)
        self.assertTemplateNotUsed(response, self.detail_template)

    def test_ies_pic_address_requirements(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        data['partner-is_ies'] = 'False'
        data['partner-pic_code'] = ''
        data['contact_address-city'] = ''
        data['contact_address-country'] = ''

        # City and country are mandatory if not ies or pic_code empty
        response = self.client.post(self.url, data, follow=True)
        self.assertIn('country', response.context_data['form_address'].errors)
        self.assertIn('city', response.context_data['form_address'].errors)
        self.assertTemplateNotUsed(response, self.detail_template)

    def test_post_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertTemplateUsed(response, self.detail_template)
        self.assertEqual(len(mail.outbox), 0)

    def test_post_as_gf_adri_notified(self):
        self.client.force_login(self.user_gf)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertTemplateUsed(response, self.detail_template)
        self.assertEqual(len(mail.outbox), 1)
        mail.outbox = []
