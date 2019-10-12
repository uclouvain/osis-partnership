from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory
from partnership.models import ContactType
from partnership.tests.factories import (
    PartnerFactory,
    PartnershipEntityManagerFactory,
    PartnerTagFactory, PartnerTypeFactory
)
from reference.tests.factories.country import CountryFactory


class PartnerCreateViewTest(TestCase):

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

        cls.user.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))
        cls.user_adri.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))
        cls.user_gf.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))
        cls.user_other_gf.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))

        # Partner creation
        cls.partner = PartnerFactory()
        cls.partner_gf = PartnerFactory(author=cls.user_gf)
        # Misc
        cls.contact_type = ContactType.objects.create(value='foobar')
        cls.country = CountryFactory()
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
        data = {
            'partner-name': 'test',
            'partner-is_valid': 'on',
            'partner-start_date': '',
            'partner-end_date': '',
            'partner-partner_type': PartnerTypeFactory().pk,
            'partner-partner_code': 'test',
            'partner-pic_code': 'test',
            'partner-erasmus_code': 'test',
            'partner-is_ies': 'True',
            'partner-is_nonprofit': 'True',
            'partner-is_public': 'True',
            'partner-use_egracons': 'on',
            'partner-comment': 'test',
            'partner-phone': 'test',
            'partner-website': 'http://localhost:8000',
            'partner-email': 'test@test.test',
            'partner-tags': [PartnerTagFactory().id],
            'contact_address-name': 'test',
            'contact_address-address': 'test',
            'contact_address-postal_code': 'test',
            'contact_address-city': 'test',
            'contact_address-country': self.country.pk,
        }
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')
