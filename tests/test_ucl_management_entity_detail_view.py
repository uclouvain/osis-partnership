from base.tests.factories.user import UserFactory
from django.test import TestCase
from django.urls import reverse
from partnership.tests.factories import UCLManagementEntityFactory


class UCLManagementEntityDetailViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.ucl_management_entity = UCLManagementEntityFactory()
        cls.user = UserFactory()
        cls.url = reverse('partnerships:ucl_management_entities:detail', kwargs={'pk': cls.ucl_management_entity.pk})

    def test_get_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_detail.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_detail.html')
