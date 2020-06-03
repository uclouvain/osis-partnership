from django.test import TestCase
from django.urls import reverse

from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory
from partnership.models import UCLManagementEntity
from partnership.tests.factories import (
    PartnershipEntityManagerFactory,
    PartnershipFactory,
    UCLManagementEntityFactory
)


class UCLManagementEntityDeleteViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        faculty = EntityFactory()
        other_faculty = EntityFactory()
        third_faculty = EntityFactory()
        EntityVersionFactory(entity_type="FACULTY", entity=faculty)
        EntityVersionFactory(entity_type="FACULTY", entity=other_faculty)
        EntityVersionFactory(entity_type="FACULTY", entity=third_faculty)

        # Users
        cls.lambda_user = UserFactory()
        cls.adri_user = UserFactory()
        entity_version = EntityVersionFactory(acronym="ADRI")
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.adri_user)
        cls.gf_user = UserFactory()
        entity_manager = PartnershipEntityManagerFactory(person__user=cls.gf_user, entity=faculty)
        cls.other_gf_user = UserFactory()
        PartnershipEntityManagerFactory(person__user=cls.other_gf_user, entity=other_faculty)

        cls.ucl_management_entity = UCLManagementEntityFactory(entity=faculty)
        cls.ucl_management_entity_linked = UCLManagementEntityFactory(
            entity=third_faculty,
        )
        PartnershipFactory(ucl_entity=third_faculty)

        cls.url = reverse(
            'partnerships:ucl_management_entities:delete',
            kwargs={"pk": cls.ucl_management_entity.pk}
        )

        cls.linked_url = reverse(
            'partnerships:ucl_management_entities:delete',
            kwargs={"pk": cls.ucl_management_entity_linked.pk},
        )
        cls.template_name = 'partnerships/ucl_management_entities/uclmanagemententity_delete.html'

    def test_get_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'access_denied.html')
        self.assertTemplateNotUsed(response, self.template_name)

    def test_get_as_authenticated(self):
        self.client.force_login(self.lambda_user)
        response = self.client.get(self.url)
        self.assertTemplateNotUsed(response, self.template_name)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_as_gf(self):
        self.client.force_login(self.gf_user)
        response = self.client.get(self.url)
        self.assertTemplateNotUsed(response, self.template_name)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_as_other_gf(self):
        self.client.force_login(self.other_gf_user)
        response = self.client.get(self.url)
        self.assertTemplateNotUsed(response, self.template_name)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_as_adri(self):
        self.client.force_login(self.adri_user)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, self.template_name)

    def test_post_as_anonymous(self):
        response = self.client.post(self.url, follow=True)
        self.assertTemplateUsed(response, 'access_denied.html')
        self.assertTemplateNotUsed(response, self.template_name)

    def test_post_as_authenticated(self):
        self.client.force_login(self.lambda_user)
        response = self.client.post(self.url)
        self.assertTemplateNotUsed(response, self.template_name)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_post_as_gf(self):
        self.client.force_login(self.gf_user)
        response = self.client.post(self.url)
        self.assertTemplateNotUsed(response, self.template_name)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_post_as_other_gf(self):
        self.client.force_login(self.other_gf_user)
        response = self.client.post(self.url)
        self.assertTemplateNotUsed(response, self.template_name)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_post_as_adri(self):
        self.client.force_login(self.adri_user)
        self.client.post(self.url)
        self.assertFalse(UCLManagementEntity.objects.filter(
            pk=self.ucl_management_entity.pk
        ))

    def test_get_for_linked_as_adri(self):
        self.client.force_login(self.adri_user)
        response = self.client.get(self.linked_url)
        self.assertTemplateNotUsed(response, self.template_name)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_post_for_linked_as_adri(self):
        self.client.force_login(self.adri_user)
        response = self.client.post(self.linked_url, follow=True)
        self.assertTemplateNotUsed(response, self.template_name)
        self.assertTemplateUsed(response, 'access_denied.html')
