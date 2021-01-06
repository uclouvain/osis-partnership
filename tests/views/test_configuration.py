from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory
from partnership.tests.factories import PartnershipEntityManagerFactory


class ConfigurationUpdateViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(
            entity=entity_version.entity,
            person__user=cls.user_adri,
        )
        cls.user_gf = UserFactory()
        PartnershipEntityManagerFactory(person__user=cls.user_gf)

        cls.url = reverse('partnerships:configuration_update')

        cls.years = AcademicYearFactory.produce(
            number_past=1,
            number_future=3,
        )

    def test_get_as_anonymous(self):
        response = self.client.get(self.url)
        self.assertTemplateNotUsed(response, 'partnerships/configuration_update.html')

    def test_get_as_user(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertTemplateNotUsed(response, 'partnerships/configuration_update.html')

    def test_get_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url)
        self.assertTemplateNotUsed(response, 'partnerships/configuration_update.html')

    def test_get_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/configuration_update.html')

    def test_post_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.post(self.url, {
            'partnership_creation_update_min_year': self.years[2].pk,
            'partnership_api_year': self.years[1].pk,
            'email_notification_to': "foo@bar.com",
        }, follow=True)
        self.assertContains(response, _('configuration_saved'))
