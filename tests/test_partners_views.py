from django.test import TestCase
from django.urls import reverse

from base.tests.factories.user import UserFactory
from partnership.tests.factories import PartnerFactory


class PartnersListView(TestCase):

    @classmethod
    def setUpTestData(cls):
        PartnerFactory()
        PartnerFactory()
        PartnerFactory()
        PartnerFactory()
        cls.user = UserFactory()
        cls.url = reverse('partnerships:partners:list')

    def test_get_list_anonymous(self):
        response = self.client.get(self.url)
        self.assertTemplateNotUsed(response, 'partnerships/partners_list.html')

    def test_get_list_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partners_list.html')
