from django.test import TestCase
from django.urls import reverse

from base.tests.factories.user import UserFactory
from partnership.tests.factories import PartnerFactory


class PartnersListView(TestCase):

    @classmethod
    def setUpTestData(cls):
        for i in range(29):
            PartnerFactory()
        cls.partner_erasmus = PartnerFactory(erasmus_code='ZZZ')
        cls.user = UserFactory()
        cls.url = reverse('partnerships:partners:list')

    def test_get_list_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners_list.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_list_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partners_list.html')

    def test_get_list_pagination(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?page=2')
        self.assertTemplateUsed(response, 'partnerships/partners_list.html')
        context = response.context_data
        self.assertEqual(len(context['partners']), 10)

    def test_get_list_ordering(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?ordering=-erasmus_code')
        self.assertTemplateUsed(response, 'partnerships/partners_list.html')
        context = response.context_data
        self.assertEqual(context['partners'][0], self.partner_erasmus)
