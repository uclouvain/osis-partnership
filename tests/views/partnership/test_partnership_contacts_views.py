from datetime import date, timedelta

from django.shortcuts import resolve_url
from django.test import TestCase

from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory
from partnership.models import ContactTitle
from partnership.tests.factories import (
    ContactFactory, ContactTypeFactory,
    PartnershipEntityManagerFactory,
    PartnershipFactory,
)


class PartnershipContactCreateViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # User creation
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.user_gf = UserFactory()
        entity_manager = PartnershipEntityManagerFactory(person__user=cls.user_gf)
        EntityVersionFactory(entity=entity_manager.entity)
        cls.user_other_gf = UserFactory()
        PartnershipEntityManagerFactory(person__user=cls.user_other_gf, entity=entity_manager.entity)

        # Partnership creation
        cls.partnership = PartnershipFactory()
        cls.partnership_gf = PartnershipFactory(
            author=cls.user_gf.person,
            ucl_entity=entity_manager.entity,
        )
        # Misc
        cls.url = resolve_url('partnerships:contacts:create', partnership_pk=cls.partnership.pk)

    def test_get_view_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/contacts/partnership_contact_create.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/contacts/partnership_contact_create.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/contacts/partnership_contact_create.html')

    def test_get_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/contacts/partnership_contact_create.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_own_as_gf(self):
        self.client.force_login(self.user_gf)
        url = resolve_url('partnerships:contacts:create', partnership_pk=self.partnership_gf.pk)
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/contacts/partnership_contact_create.html')

    def test_get_from_faculty_as_gf(self):
        self.client.force_login(self.user_other_gf)
        url = resolve_url('partnerships:contacts:create', partnership_pk=self.partnership_gf.pk)
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/contacts/partnership_contact_create.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        data = {
            'title': ContactTitle.MISTER.name,
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
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')


class PartnershipContactUpdateViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # User creation
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.user_gf = UserFactory()
        entity_manager = PartnershipEntityManagerFactory(person__user=cls.user_gf)
        EntityVersionFactory(entity=entity_manager.entity)
        cls.user_other_gf = UserFactory()
        PartnershipEntityManagerFactory(person__user=cls.user_other_gf, entity=entity_manager.entity)

        # Partnership creation
        contact = ContactFactory()
        cls.partnership = PartnershipFactory(contacts=[contact])
        cls.url = resolve_url(
            'partnerships:contacts:update',
            partnership_pk=cls.partnership.pk,
            pk=contact.pk,
        )

        contact = ContactFactory()
        cls.partnership_gf = PartnershipFactory(
            author=cls.user_gf.person,
            ucl_entity=entity_manager.entity,
            contacts=[contact],
        )
        cls.gf_url = resolve_url(
            'partnerships:contacts:update',
            partnership_pk=cls.partnership_gf.pk,
            pk=contact.pk,
        )

    def test_get_view_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/contacts/partnership_contact_update.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/contacts/partnership_contact_update.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/contacts/partnership_contact_update.html')

    def test_get_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/contacts/partnership_contact_update.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_own_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.gf_url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/contacts/partnership_contact_update.html')

    def test_get_from_faculty_as_gf(self):
        self.client.force_login(self.user_other_gf)
        response = self.client.get(self.gf_url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/contacts/partnership_contact_update.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        data = {
            'title': ContactTitle.MISTER.name,
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
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')


class PartnershipContactDeleteViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # User creation
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.user_gf = UserFactory()
        entity_manager = PartnershipEntityManagerFactory(person__user=cls.user_gf)
        EntityVersionFactory(entity=entity_manager.entity)
        cls.user_other_gf = UserFactory()
        PartnershipEntityManagerFactory(person__user=cls.user_other_gf, entity=entity_manager.entity)

        # Partnership creation
        contact = ContactFactory()
        cls.partnership = PartnershipFactory(contacts=[contact])
        cls.url = resolve_url(
            'partnerships:contacts:delete',
            partnership_pk=cls.partnership.pk,
            pk=contact.pk,
        )

        contact = ContactFactory()
        cls.partnership_gf = PartnershipFactory(
            author=cls.user_gf.person,
            ucl_entity=entity_manager.entity,
            contacts=[contact],
        )
        cls.gf_url = resolve_url(
            'partnerships:contacts:delete',
            partnership_pk=cls.partnership_gf.pk,
            pk=contact.pk,
        )

    def test_get_view_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/contacts/contact_confirm_delete.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/contacts/contact_confirm_delete.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/contacts/contact_confirm_delete.html')

    def test_get_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/contacts/contact_confirm_delete.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_own_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.gf_url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/contacts/contact_confirm_delete.html')

    def test_get_from_faculty_as_gf(self):
        self.client.force_login(self.user_other_gf)
        response = self.client.get(self.gf_url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/contacts/contact_confirm_delete.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        data = {}
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')
