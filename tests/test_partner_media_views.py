from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory
from partnership.models import ContactType, Media
from partnership.tests.factories import (
    MediaFactory, PartnerFactory,
    PartnershipEntityManagerFactory
)
from reference.tests.factories.country import CountryFactory


class PartnerMediaCreateViewTest(TestCase):

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
        cls.url = reverse('partnerships:partners:medias:create', kwargs={'partner_pk': cls.partner.pk})

    def test_get_view_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/medias/partner_media_create.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/medias/partner_media_create.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partners/medias/partner_media_create.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        data = {
            'name': 'test',
            'description': 'test',
            'url': 'http://example.com',
            'visibility': Media.VISIBILITY_PUBLIC,
        }
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')


class PartnerMediaUpdateViewTest(TestCase):

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
        cls.media = MediaFactory()
        cls.partner.medias.add(cls.media)
        cls.url = reverse('partnerships:partners:medias:update',
                          kwargs={'partner_pk': cls.partner.pk, 'pk': cls.media.pk})

    def test_get_view_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/medias/partner_media_update.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/medias/partner_media_update.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partners/medias/partner_media_update.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        data = {
            'name': 'test',
            'description': 'test',
            'url': 'http://example.com',
            'visibility': Media.VISIBILITY_PUBLIC,
        }
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')


class PartnerMediaDeleteViewTest(TestCase):

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
        cls.media = MediaFactory()
        cls.partner.medias.add(cls.media)
        cls.url = reverse('partnerships:partners:medias:delete',
                          kwargs={'partner_pk': cls.partner.pk, 'pk': cls.media.pk})

    def test_get_view_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/medias/partner_media_delete.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/medias/partner_media_delete.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partners/medias/partner_media_delete.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        data = {}
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')
