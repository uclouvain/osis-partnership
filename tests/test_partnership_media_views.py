from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory
from partnership.models import Media
from partnership.tests.factories import (MediaFactory, PartnershipEntityManagerFactory, PartnershipFactory)


class PartnershipMediaCreateViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # User creation
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.user_adri)

        cls.user.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))
        cls.user_adri.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))

        # Partnership creation
        cls.partnership = PartnershipFactory()
        # Misc
        cls.url = reverse('partnerships:medias:create', kwargs={'partnership_pk': cls.partnership.pk})

    def test_get_view_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/medias/partnership_media_create.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/medias/partnership_media_create.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/medias/partnership_media_create.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        data = {
            'name': 'test',
            'description': 'test',
            'url': 'http://example.com',
            'visibility': Media.VISIBILITY_PUBLIC,
        }
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership_detail.html')


class PartnershipMediaUpdateViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # User creation
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.user_adri)

        cls.user.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))
        cls.user_adri.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))

        # Partnership creation
        cls.partnership = PartnershipFactory()
        # Misc
        cls.media = MediaFactory()
        cls.partnership.medias.add(cls.media)
        cls.url = reverse('partnerships:medias:update',
                          kwargs={'partnership_pk': cls.partnership.pk, 'pk': cls.media.pk})

    def test_get_view_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/medias/partnership_media_update.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/medias/partnership_media_update.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/medias/partnership_media_update.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        data = {
            'name': 'test',
            'description': 'test',
            'url': 'http://example.com',
            'visibility': Media.VISIBILITY_PUBLIC,
        }
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership_detail.html')


class PartnershipMediaDeleteViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # User creation
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.user_adri)

        cls.user.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))
        cls.user_adri.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))

        # Partnership creation
        cls.partnership = PartnershipFactory()
        # Misc
        cls.media = MediaFactory()
        cls.partnership.medias.add(cls.media)
        cls.url = reverse('partnerships:medias:delete',
                          kwargs={'partnership_pk': cls.partnership.pk, 'pk': cls.media.pk})

    def test_get_view_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/medias/partnership_media_delete.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/medias/partnership_media_delete.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/medias/partnership_media_delete.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        data = {}
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership_detail.html')
