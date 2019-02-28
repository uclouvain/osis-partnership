from django.test import TestCase
from django.urls import reverse

from base.tests.factories.user import UserFactory
from partnership.tests.factories import PartnershipFactory


class PartnershipDetailViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.partnership = PartnershipFactory()
        cls.user = UserFactory()
        cls.url = reverse('partnerships:detail', kwargs={'pk': cls.partnership.pk})

    def test_get_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnership_detail.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partnership_detail.html')
