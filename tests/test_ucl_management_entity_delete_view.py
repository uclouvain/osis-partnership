from django.test import TestCase
from django.urls import reverse
from partnership.tests.factories import UCLManagementEntityFactory
from base.tests.factories.user import UserFactory
from partnership.models import UCLManagementEntity

class UCLManagementEntityDeleteViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.ucl_management_entity = UCLManagementEntityFactory()
        cls.user = UserFactory()
        cls.url = reverse(
            'partnership:ucl_management_entity:delete',
            kwargs={"pk": cls.ucl_management_entity.pk}
        )

    def test_get_as_anonymous(cls):
        response = self.client.get(self.url)
        self.assertTemplateUsed('registration/login.html')
        self.assertTemplateNotUsed('partnerships/ucl_management_entity/uclmanagemententity_delete.html')

    def test_get_as_authenticated(cls):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertTemplateUsed('partnerships/ucl_management_entity/uclmanagemententity_delete.html')

    def test_post_as_authenticated(cls):
        self.client.force_login(self.user)
        response = self.client.post(self.post)
        self.assertFalse(UCLManagementEntity.objects.get(pk=self.ucl_management_entity.pk).exists())
