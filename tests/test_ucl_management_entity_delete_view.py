from django.test import TestCase
from django.urls import reverse
from partnership.tests.factories import UCLManagementEntityFactory
from base.tests.factories.user import UserFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.entity_manager import EntityManagerFactory
from base.tests.factories.person_entity import PersonEntityFactory
from partnership.models import UCLManagementEntity

class UCLManagementEntityDeleteViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        faculty = EntityFactory()
        other_faculty = EntityFactory()
        EntityVersionFactory(entity_type="FACULTY", entity=faculty)
        EntityVersionFactory(entity_type="FACULTY", entity=other_faculty)

        # Users
        cls.lambda_user = UserFactory()
        cls.adri_user = UserFactory()
        entity_version = EntityVersionFactory(acronym="ADRI")
        PersonEntityFactory(entity=entity_version.entity, person__user=cls.adri_user)
        cls.gf_user = UserFactory()
        entity_manager = EntityManagerFactory(person__user=cls.gf_user, entity=faculty)
        cls.other_gf_user = UserFactory()
        EntityManagerFactory(person__user=cls.other_gf_user, entity=other_faculty)

        cls.ucl_management_entity = UCLManagementEntityFactory(faculty=faculty)

        cls.url = reverse(
            'partnerships:ucl_management_entities:delete',
            kwargs={"pk": cls.ucl_management_entity.pk}
        )

    def test_get_as_anonymous(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed('registration/login.html')
        self.assertTemplateNotUsed('partnerships/ucl_management_entity/uclmanagemententity_delete.html')

    def test_get_as_authenticated(self):
        self.client.force_login(self.lambda_user)
        response = self.client.get(self.url)
        self.assertTemplateNotUsed('partnerships/ucl_management_entity/uclmanagemententity_delete.html')
        self.assertTemplateUsed('registration/login.html')

    def test_get_as_gf(self):
        self.client.force_login(self.gf_user)
        response = self.client.get(self.url)
        self.assertTemplateNotUsed('partnerships/ucl_management_entity/uclmanagemententity_delete.html')
        self.assertTemplateUsed('registration/login.html')

    def test_get_as_other_gf(self):
        self.client.force_login(self.other_gf_user)
        response = self.client.get(self.url)
        self.assertTemplateNotUsed('partnerships/ucl_management_entity/uclmanagemententity_delete.html')
        self.assertTemplateUsed('registration/login.html')

    def test_get_as_adri(self):
        self.client.force_login(self.other_gf_user)
        response = self.client.get(self.url)
        self.assertTemplateUsed('partnerships/ucl_management_entity/uclmanagemententity_delete.html')

    def test_post_as_anonymous(self):
        response = self.client.post(self.url)
        self.assertTemplateUsed('registration/login.html')
        self.assertTemplateNotUsed('partnerships/ucl_management_entity/uclmanagemententity_delete.html')

    def test_post_as_authenticated(self):
        self.client.force_login(self.lambda_user)
        response = self.client.post(self.url)
        self.assertTemplateNotUsed('partnerships/ucl_management_entity/uclmanagemententity_delete.html')
        self.assertTemplateUsed('registration/login.html')

    def test_post_as_gf(self):
        self.client.force_login(self.gf_user)
        response = self.client.post(self.url)
        self.assertTemplateNotUsed('partnerships/ucl_management_entity/uclmanagemententity_delete.html')
        self.assertTemplateUsed('registration/login.html')

    def test_post_as_other_gf(self):
        self.client.force_login(self.other_gf_user)
        response = self.client.post(self.url)
        self.assertTemplateNotUsed('partnerships/ucl_management_entity/uclmanagemententity_delete.html')
        self.assertTemplateUsed('registration/login.html')

    def test_post_as_adri(self):
        self.client.force_login(self.adri_user)
        response = self.client.post(self.url)
        self.assertFalse(UCLManagementEntity.objects.filter(pk=self.ucl_management_entity.pk).exists())
