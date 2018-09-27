from base.tests.factories.user import UserFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_manager import EntityManagerFactory
from base.tests.factories.person_entity import PersonEntityFactory
from django.test import TestCase
from django.urls import reverse
from partnership.tests.factories import UCLManagementEntityFactory

class UCLManagementEntityDetailViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        faculty = EntityFactory()
        entity_version = EntityVersionFactory(entity_type="FACULTY", entity=faculty)


        cls.ucl_management_entity = UCLManagementEntityFactory(faculty=faculty)

        # Users
        cls.lambda_user = UserFactory()
        cls.adri_user = UserFactory()
        entity_version = EntityVersionFactory(acronym="ADRI")
        PersonEntityFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.gf_user = UserFactory()
        entity_manager = EntityManagerFactory(person__user=cls.user_gf)
        cls.other_gf_user = UserFactory()
        EntityManagerFactory(person__user=cls.other_gf_user, entity=entity_manager.entity)

        entity_manger = EntityManagerFactory(entity=faculty, person=cls.gf_user.person)


        cls.url = reverse('partnerships:ucl_management_entities:detail', kwargs={'pk': cls.ucl_management_entity.pk})

    def test_get_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_detail.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_authenticated(self):
        self.client.force_login(self.lambda_user)
        response = self.client.get(self.url)
        self.assertTemplateNotUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_detail.html')
        self.assertEqual(response.status_code, 403)

    def test_get_gf(self):
        self.client.force_login(self.gf_user)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_detail.html')

    def test_get_other_gf(self):
        self.client.force_login(self.other_gf_user)
        response = self.client.get(self.url)
        self.assertTemplateNotUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_detail.html')
        self.assertEqual(response.status_code, 403)

    def test_get_adri(self):
        self.client.force_login(self.adri_user)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_detail.html')
