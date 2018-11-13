from django.test import TestCase
from django.urls import reverse

from partnership.tests.factories import PartnershipEntityManagerFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory
from partnership.models import ContactType, Media
from partnership.tests.factories import MediaFactory, PartnerFactory
from reference.tests.factories.country import CountryFactory


class PartnerEntityCreateViewTest(TestCase):

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
        cls.partner_gf = PartnerFactory(author=cls.user_gf)
        # Misc
        cls.contact_type = ContactType.objects.create(value='foobar')
        cls.country = CountryFactory()
        cls.url = reverse('partnerships:partners:entities:create', kwargs={'partner_pk': cls.partner.pk})

    def test_get_view_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/entities/partner_entity_create.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_view_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/entities/partner_entity_create.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partners/entities/partner_entity_create.html')

    def test_get_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partners/entities/partner_entity_create.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        data = {
            'name': 'test',
            'comment': 'test',
            'address_name': 'test',
            'address_address': 'test',
            'address_postal_code': '13245',
            'address_city': 'test',
            'address_country': self.country.pk,
            'contact_in_type': self.contact_type.pk,
            'contact_in_title': 'mr',
            'contact_in_last_name': 'test',
            'contact_in_first_name': 'test',
            'contact_in_function': 'test',
            'contact_in_phone': 'test',
            'contact_in_mobile_phone': 'test',
            'contact_in_fax': 'test',
            'contact_in_email': 'test@test.test',
            'contact_out_type': self.contact_type.pk,
            'contact_out_title': 'mr',
            'contact_out_last_name': 'test',
            'contact_out_first_name': 'test',
            'contact_out_function': 'test',
            'contact_out_phone': 'test',
            'contact_out_mobile_phone': 'test',
            'contact_out_fax': 'test',
            'contact_out_email': 'test@test.test',
            'parent': '',
        }
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')


class PartnerEntityUpdateViewTest(TestCase):

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
        cls.partner_gf = PartnerFactory(author=cls.user_gf)
        # Misc
        cls.contact_type = ContactType.objects.create(value='foobar')
        cls.country = CountryFactory()
        cls.partner_entity = cls.partner.entities.first()
        cls.url = reverse('partnerships:partners:entities:update',
                          kwargs={'partner_pk': cls.partner.pk, 'pk': cls.partner_entity.pk})

    def test_get_view_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/entities/partner_entity_update.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_view_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/entities/partner_entity_update.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partners/entities/partner_entity_update.html')

    def test_get_other_partner_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/entities/partner_entity_update.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_own_partner_as_gf(self):
        self.client.force_login(self.user_gf)
        url = reverse('partnerships:partners:entities:update',
                      kwargs={'partner_pk': self.partner_gf.pk, 'pk': self.partner_gf.entities.first().pk})
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/entities/partner_entity_update.html')

    def test_get_faculty_partner_as_gf(self):
        self.client.force_login(self.user_other_gf)
        url = reverse('partnerships:partners:entities:update',
                      kwargs={'partner_pk': self.partner_gf.pk, 'pk': self.partner_gf.entities.first().pk})
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/entities/partner_entity_update.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        data = {
            'name': 'test',
            'comment': 'test',
            'address_name': 'test',
            'address_address': 'test',
            'address_postal_code': '13245',
            'address_city': 'test',
            'address_country': self.country.pk,
            'contact_in_type': self.contact_type.pk,
            'contact_in_title': 'mr',
            'contact_in_last_name': 'test',
            'contact_in_first_name': 'test',
            'contact_in_function': 'test',
            'contact_in_phone': 'test',
            'contact_in_mobile_phone': 'test',
            'contact_in_fax': 'test',
            'contact_in_email': 'test@test.test',
            'contact_out_type': self.contact_type.pk,
            'contact_out_title': 'mr',
            'contact_out_last_name': 'test',
            'contact_out_first_name': 'test',
            'contact_out_function': 'test',
            'contact_out_phone': 'test',
            'contact_out_mobile_phone': 'test',
            'contact_out_fax': 'test',
            'contact_out_email': 'test@test.test',
            'parent': '',
        }
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')


class PartnerEntityDeleteViewTest(TestCase):

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
        cls.partner_gf = PartnerFactory(author=cls.user_gf)
        # Misc
        cls.contact_type = ContactType.objects.create(value='foobar')
        cls.country = CountryFactory()
        cls.partner_entity = cls.partner.entities.first()
        cls.url = reverse('partnerships:partners:entities:delete',
                          kwargs={'partner_pk': cls.partner.pk, 'pk': cls.partner_entity.pk})

    def test_get_view_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/entities/partner_entity_delete.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_view_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/entities/partner_entity_delete.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partners/entities/partner_entity_delete.html')

    def test_get_other_partner_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/entities/partner_entity_delete.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_own_partner_as_gf(self):
        self.client.force_login(self.user_gf)
        url = reverse('partnerships:partners:entities:delete',
                      kwargs={'partner_pk': self.partner_gf.pk, 'pk': self.partner_gf.entities.first().pk})
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/entities/partner_entity_delete.html')

    def test_get_faculty_partner_as_gf(self):
        self.client.force_login(self.user_other_gf)
        url = reverse('partnerships:partners:entities:delete',
                      kwargs={'partner_pk': self.partner_gf.pk, 'pk': self.partner_gf.entities.first().pk})
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/entities/partner_entity_delete.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        data = {}
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')
