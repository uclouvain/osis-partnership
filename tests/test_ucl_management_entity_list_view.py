from django.test import TestCase
from django.urls import reverse

from base.models.enums.entity_type import FACULTY
from base.tests.factories.entity import EntityFactory
from partnership.tests.factories import PartnershipEntityManagerFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory
from partnership.tests.factories import UCLManagementEntityFactory

GF_UME_NUMBER = 3
OTHER_GF_UME_NUMBER = 7


class UCLManagementEntitiesListViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        sector = EntityFactory()
        faculty = EntityFactory()
        EntityVersionFactory(entity=faculty, parent=sector, entity_type=FACULTY)
        other_faculty = EntityFactory()
        EntityVersionFactory(entity_type="FACULTY", entity=faculty)
        EntityVersionFactory(entity_type="FACULTY", entity=other_faculty)

        # Users
        cls.lambda_user = UserFactory()
        cls.adri_user = UserFactory()
        entity_version = EntityVersionFactory(acronym="ADRI")
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.adri_user)
        cls.gs_user = UserFactory()
        PartnershipEntityManagerFactory(person__user=cls.gs_user, entity=sector)
        cls.gf_user = UserFactory()
        PartnershipEntityManagerFactory(person__user=cls.gf_user, entity=faculty)
        cls.other_gf_user = UserFactory()
        PartnershipEntityManagerFactory(person__user=cls.other_gf_user, entity=other_faculty)

        for i in range(GF_UME_NUMBER):
            UCLManagementEntityFactory(faculty=faculty)
        for i in range(OTHER_GF_UME_NUMBER):
            UCLManagementEntityFactory(faculty=other_faculty)

        cls.url = reverse('partnerships:ucl_management_entities:list')

    def test_get_list_anonynmous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_list.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_list_authenticated(self):
        self.client.force_login(self.lambda_user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_list.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_list_gf(self):
        self.client.force_login(self.gf_user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_list.html')
        self.assertEqual(len(response.context['ucl_management_entities']), GF_UME_NUMBER)

    def test_get_list_other_gf(self):
        self.client.force_login(self.other_gf_user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_list.html')
        self.assertEqual(len(response.context['ucl_management_entities']), OTHER_GF_UME_NUMBER)

    def test_get_list_adri(self):
        self.client.force_login(self.adri_user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_list.html')
        self.assertEqual(len(response.context['ucl_management_entities']), OTHER_GF_UME_NUMBER + GF_UME_NUMBER)

    def test_get_list_gs(self):
        self.client.force_login(self.gs_user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_list.html')
        self.assertEqual(len(response.context['ucl_management_entities']), GF_UME_NUMBER)
