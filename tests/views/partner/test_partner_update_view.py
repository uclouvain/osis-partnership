from datetime import timedelta

from django.test import TestCase
from django.urls import reverse

from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory
from partnership.models import ContactType, Partner
from partnership.tests.factories import (
    PartnerFactory,
    PartnerTagFactory,
    PartnershipEntityManagerFactory,
)
from reference.tests.factories.country import CountryFactory


class PartnerUpdateViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # User creation
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.user_gf = UserFactory()
        entity_manager = PartnershipEntityManagerFactory(person__user=cls.user_gf)
        cls.user_other_gf = UserFactory()
        PartnershipEntityManagerFactory(person__user=cls.user_other_gf, entity=entity_manager.entity)

        # Partner creation
        cls.partner = PartnerFactory()
        cls.partner_gf = PartnerFactory(author=cls.user_gf.person)
        # Misc
        cls.country = CountryFactory()

        cls.data = {
            'organization-name': 'test',
            'partner-is_valid': 'on',
            'organization-start_date': cls.partner.organization.start_date,
            'organization-end_date': '',
            'organization-type':  cls.partner.organization.type,
            'organization-code': 'test',
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
            'contact_address-location_0': 10,
            'contact_address-location_1': -12,
        }

        cls.url = reverse('partnerships:partners:update', kwargs={'pk': cls.partner.pk})

    def test_get_partner_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/partner_update.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_partner_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/partner_update.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_partner_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_update.html')

    def test_get_other_partner_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/partner_update.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_own_partner_as_gf(self):
        self.client.force_login(self.user_gf)
        url = reverse('partnerships:partners:update', kwargs={'pk': self.partner_gf.pk})
        response = self.client.get(url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/partner_update.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_faculty_partner_as_gf(self):
        self.client.force_login(self.user_other_gf)
        url = reverse('partnerships:partners:update', kwargs={'pk': self.partner_gf.pk})
        response = self.client.get(url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/partner_update.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')

    def test_repost_and_not_ies(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        data['partner-pic_code'] = ''
        data['partner-is_ies'] = 'False'
        data['partner-contact_type'] = Partner.CONTACT_TYPE_CHOICES[-1][0]

        # City and country are mandatory if not ies or pic_code empty, but provided
        response = self.client.post(self.url, data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')

        # If we repost it with same data, should not fail
        response = self.client.post(self.url, data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')

    def test_post_new_dates(self):
        self.client.force_login(self.user_adri)
        entity = self.partner.organization.entity_set.first()
        self.assertEqual(entity.entityversion_set.count(), 1)
        data = self.data.copy()
        data['organization-start_date'] = self.partner.organization.start_date + timedelta(days=30)
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')
        self.assertEqual(entity.entityversion_set.count(), 2)

    def test_post_end_date(self):
        self.client.force_login(self.user_adri)
        entity = self.partner.organization.entity_set.first()
        self.assertEqual(entity.entityversion_set.count(), 1)
        data = self.data.copy()
        data['organization-end_date'] = self.partner.organization.start_date + timedelta(days=30)
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')
        self.assertEqual(entity.entityversion_set.count(), 1)

    def test_post_both_dates(self):
        self.client.force_login(self.user_adri)
        entity = self.partner.organization.entity_set.first()
        self.assertEqual(entity.entityversion_set.count(), 1)
        data = self.data.copy()
        data['organization-start_date'] = self.partner.organization.start_date + timedelta(days=30)
        data['organization-end_date'] = self.partner.organization.start_date + timedelta(days=60)
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')
        self.assertEqual(entity.entityversion_set.count(), 2)
