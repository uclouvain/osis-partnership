from django.test import TestCase

from partnership.tests.factories import PartnershipFactory
from base.tests.factories.user import UserFactory

class PartnershipsListViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        for i in range(21):
            PartnershipFactory(is_valid=True)
        cls.partnership_not_valid = PartnershipFactory(is_valid=False)
        cls.user = UserFactory
        cls.url = reverse('partnerships:partnerships_list')
        
    def test_sort_not_valid():
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?ordering=-is_valid')
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
                                
    def test_sort_not_valid_ajax():
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?ordering=-is_valid',
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTemplateUsed(response, 'partnerships/includes/partnerships_list_result.html')
