from django.test import TestCase
from django.urls import reverse

from partnership.tests.factories import (
    PartnerFactory,
    PartnershipEntityManagerFactory,
)


class PartnersSimilarViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        PartnerFactory(organization__name='foo')
        PartnerFactory(organization__name='Foobar')
        PartnerFactory(organization__name='FooBarBaz')
        cls.user = PartnershipEntityManagerFactory().person.user
        cls.url = reverse('partnerships:partners:similar')
        cls.template_name = 'partnerships/partners/includes/similar_partners_preview.html'

    def test_get_list_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, self.template_name)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_list_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, self.template_name)

    def test_get_not_enough_letters(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?search=fo')
        self.assertTemplateUsed(response, self.template_name)
        context = response.context_data
        self.assertEqual(len(context['similar_partners']), 0)

    def test_get_similar(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?search=foo')
        self.assertTemplateUsed(response, self.template_name)
        context = response.context_data
        self.assertEqual(len(context['similar_partners']), 3)
