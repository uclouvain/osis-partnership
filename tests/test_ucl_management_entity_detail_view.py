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
        other_faculty = EntityFactory()
        EntityVersionFactory(entity_type="FACULTY", entity=faculty)
        EntityVersionFactory(entity_type="FACULTY", entity=other_faculty)

        cls.ucl_management_entity = UCLManagementEntityFactory(faculty=faculty)

        # Users
        cls.lambda_user = UserFactory()
        cls.adri_user = UserFactory()
        entity_version = EntityVersionFactory(acronym="ADRI")
        PersonEntityFactory(entity=entity_version.entity, person__user=cls.adri_user)
        cls.gf_user = UserFactory()
        entity_manager = EntityManagerFactory(person__user=cls.gf_user, entity=faculty)
        cls.other_gf_user = UserFactory()
        EntityManagerFactory(person__user=cls.other_gf_user, entity=other_faculty)

        cls.url = reverse('partnerships:ucl_management_entities:detail', kwargs={'pk': cls.ucl_management_entity.pk})

    def test_get_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_detail.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_authenticated(self):
        self.client.force_login(self.lambda_user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_detail.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_gf(self):
        self.client.force_login(self.gf_user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_detail.html')

    def test_get_other_gf(self):
        self.client.force_login(self.other_gf_user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_detail.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_adri(self):
        self.client.force_login(self.adri_user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_detail.html')
