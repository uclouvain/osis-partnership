from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from base.tests.factories.entity_manager import EntityManagerFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.user import UserFactory
from partnership.tests.factories import PartnershipFactory, ContactTypeFactory


class PartnershipContactCreateViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # User creation
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PersonEntityFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.user_gf = UserFactory()
        entity_manager = EntityManagerFactory(person__user=cls.user_gf)
        cls.user_other_gf = UserFactory()
        EntityManagerFactory(person__user=cls.user_other_gf, entity=entity_manager.entity)
        # Partnership creation
        date_ok = date.today() + timedelta(days=365)
        date_ko = date.today() - timedelta(days=365)
        cls.partnership = PartnershipFactory(start_date=date_ok)
        cls.partnership_gf = PartnershipFactory(start_date=date_ok, author=cls.user_gf)
        cls.partnership_out_of_date = PartnershipFactory(start_date=date_ko, author=cls.user_gf)
        # Misc
        cls.url = reverse('partnerships:contacts:create', kwargs={'partnership_pk': cls.partnership.pk})

    def test_get_view_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/contacts/partnership_contact_create.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_view_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/contacts/partnership_contact_create.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/contacts/partnership_contact_create.html')

    def test_get_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/contacts/partnership_contact_create.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_own_as_gf(self):
        self.client.force_login(self.user_gf)
        url = reverse('partnerships:contacts:create', kwargs={'partnership_pk': self.partnership_gf.pk})
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/contacts/partnership_contact_create.html')

    def test_get_from_faculty_as_gf(self):
        self.client.force_login(self.user_other_gf)
        url = reverse('partnerships:contacts:create', kwargs={'partnership_pk': self.partnership_gf.pk})
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/contacts/partnership_contact_create.html')

    def test_get_out_of_date_as_adri(self):
        self.client.force_login(self.user_adri)
        url = reverse('partnerships:contacts:create', kwargs={'partnership_pk': self.partnership_out_of_date.pk})
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/contacts/partnership_contact_create.html')

    def test_get_out_of_date_as_gf(self):
        self.client.force_login(self.user_gf)
        url = reverse('partnerships:contacts:create', kwargs={'partnership_pk': self.partnership_out_of_date.pk})
        response = self.client.get(url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/contacts/partnership_contact_create.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        data = {
            'title': 'mr',
            'type': ContactTypeFactory().pk,
            'last_name': 'test',
            'first_name': 'test',
            'society': 'test',
            'function': 'test',
            'phone': 'test',
            'mobile_phone': 'test',
            'fax': 'test',
            'email': 'test@example.com',
            'comment': 'test',
        }
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership_detail.html')


class PartnershipContactUpdateViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # User creation
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PersonEntityFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.user_gf = UserFactory()
        entity_manager = EntityManagerFactory(person__user=cls.user_gf)
        cls.user_other_gf = UserFactory()
        EntityManagerFactory(person__user=cls.user_other_gf, entity=entity_manager.entity)
        # Partnership creation
        date_ok = date.today() + timedelta(days=365)
        date_ko = date.today() - timedelta(days=365)
        cls.partnership = PartnershipFactory(start_date=date_ok)
        cls.partnership_gf = PartnershipFactory(start_date=date_ok, author=cls.user_gf)
        cls.partnership_out_of_date = PartnershipFactory(start_date=date_ko, author=cls.user_gf)
        # Misc
        cls.url = reverse('partnerships:contacts:update', kwargs={
            'partnership_pk': cls.partnership.pk, 'pk': cls.partnership.contacts.all()[0].pk
        })

    def test_get_view_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/contacts/partnership_contact_update.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_view_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/contacts/partnership_contact_update.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/contacts/partnership_contact_update.html')

    def test_get_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/contacts/partnership_contact_update.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_own_as_gf(self):
        self.client.force_login(self.user_gf)
        url = reverse('partnerships:contacts:update', kwargs={
            'partnership_pk': self.partnership_gf.pk, 'pk': self.partnership_gf.contacts.all()[0].pk
        })
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/contacts/partnership_contact_update.html')

    def test_get_from_faculty_as_gf(self):
        self.client.force_login(self.user_other_gf)
        url = reverse('partnerships:contacts:update', kwargs={
            'partnership_pk': self.partnership_gf.pk, 'pk': self.partnership_gf.contacts.all()[0].pk
        })
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/contacts/partnership_contact_update.html')

    def test_get_out_of_date_as_adri(self):
        self.client.force_login(self.user_adri)
        url = reverse('partnerships:contacts:update', kwargs={
            'partnership_pk': self.partnership_out_of_date.pk, 'pk': self.partnership_out_of_date.contacts.all()[0].pk
        })
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/contacts/partnership_contact_update.html')

    def test_get_out_of_date_as_gf(self):
        self.client.force_login(self.user_gf)
        url = reverse('partnerships:contacts:update', kwargs={
            'partnership_pk': self.partnership_out_of_date.pk, 'pk': self.partnership_out_of_date.contacts.all()[0].pk
        })
        response = self.client.get(url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/contacts/partnership_contact_update.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        data = {
            'title': 'mr',
            'type': ContactTypeFactory().pk,
            'last_name': 'test',
            'first_name': 'test',
            'society': 'test',
            'function': 'test',
            'phone': 'test',
            'mobile_phone': 'test',
            'fax': 'test',
            'email': 'test@example.com',
            'comment': 'test',
        }
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership_detail.html')


class PartnershipContactDeleteViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # User creation
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PersonEntityFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.user_gf = UserFactory()
        entity_manager = EntityManagerFactory(person__user=cls.user_gf)
        cls.user_other_gf = UserFactory()
        EntityManagerFactory(person__user=cls.user_other_gf, entity=entity_manager.entity)
        # Partnership creation
        date_ok = date.today() + timedelta(days=365)
        date_ko = date.today() - timedelta(days=365)
        cls.partnership = PartnershipFactory(start_date=date_ok)
        cls.partnership_gf = PartnershipFactory(start_date=date_ok, author=cls.user_gf)
        cls.partnership_out_of_date = PartnershipFactory(start_date=date_ko, author=cls.user_gf)
        # Misc
        cls.url = reverse('partnerships:contacts:delete', kwargs={
            'partnership_pk': cls.partnership.pk, 'pk': cls.partnership.contacts.all()[0].pk
        })

    def test_get_view_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/contacts/contact_confirm_delete.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_view_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/contacts/contact_confirm_delete.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/contacts/contact_confirm_delete.html')

    def test_get_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/contacts/contact_confirm_delete.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_own_as_gf(self):
        self.client.force_login(self.user_gf)
        url = reverse('partnerships:contacts:delete', kwargs={
            'partnership_pk': self.partnership_gf.pk, 'pk': self.partnership_gf.contacts.all()[0].pk
        })
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/contacts/contact_confirm_delete.html')

    def test_get_from_faculty_as_gf(self):
        self.client.force_login(self.user_other_gf)
        url = reverse('partnerships:contacts:delete', kwargs={
            'partnership_pk': self.partnership_gf.pk, 'pk': self.partnership_gf.contacts.all()[0].pk
        })
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/contacts/contact_confirm_delete.html')

    def test_get_out_of_date_as_adri(self):
        self.client.force_login(self.user_adri)
        url = reverse('partnerships:contacts:delete', kwargs={
            'partnership_pk': self.partnership_out_of_date.pk, 'pk': self.partnership_out_of_date.contacts.all()[0].pk
        })
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/contacts/contact_confirm_delete.html')

    def test_get_out_of_date_as_gf(self):
        self.client.force_login(self.user_gf)
        url = reverse('partnerships:contacts:delete', kwargs={
            'partnership_pk': self.partnership_out_of_date.pk, 'pk': self.partnership_out_of_date.contacts.all()[0].pk
        })
        response = self.client.get(url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/contacts/contact_confirm_delete.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        data = {}
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership_detail.html')