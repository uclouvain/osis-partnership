from django.test import TestCase
from django.urls import reverse

from partnership.tests.factories import (
    PartnerFactory,
    PartnershipEntityManagerFactory,
)


class PartnerDetailViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.partner = PartnerFactory()
        cls.user = PartnershipEntityManagerFactory().person.user
        cls.url = reverse('partnerships:partners:detail', kwargs={'pk': cls.partner.pk})

    def test_get_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/partner_detail.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')
