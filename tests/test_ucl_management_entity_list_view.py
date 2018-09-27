from django.test import TestCase
from partnership.tests.factories import UCLManagementEntityFactory
from base.tests.factories.user import UserFactory
from django.urls import reverse

class UCLManagementEntitiesListViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        for i in range(15):
            UCLManagementEntityFactory()
        cls.url = reverse('partnerships:ucl_management_entities:list')

    def test_get_list_anonynmous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_list.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_list_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_list.html')
