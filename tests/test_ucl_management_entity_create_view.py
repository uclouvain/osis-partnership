from django.test import TestCase
from django.urls import reverse
from base.tests.factories.user import UserFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.models.enums.entity_type import FACULTY
from django.urls import reverse


class UCLManagementEntityCreateViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.url = reverse("partnerships:ucl_management_entities:create")

        # Data :
        cls.faculty = EntityFactory()
        EntityVersionFactory(entity=cls.faculty, entity_type=FACULTY)
        cls.entity = EntityFactory()
        cls.academic_responsible = PersonFactory()
        cls.administrative_responsible = PersonFactory()
        cls.contact_in_person = PersonFactory()
        cls.contact_out_person = PersonFactory()

        cls.data = {
            'academic_responsible': str(cls.academic_responsible.pk),
            'administrative_responsible': str(cls.administrative_responsible.pk),
            'contact_in_email': 'foo@foo.fr',
            'contact_in_person': str(cls.contact_in_person.pk),
            'contact_in_url': 'http://foo.fr/foo',
            'contact_out_email': 'bar@bar.fr',
            'contact_out_person': str(cls.contact_out_person.pk),
            'contact_out_url': 'http://bar.fr/bar',
            'entity': str(cls.entity.pk),
            'faculty': str(cls.faculty.pk),
        }

    def test_get_view_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_create.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_view_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed('partnerships/ucl_management_entities/uclmanagemententity_create.html')

    def test_post(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/ucl_management_entity/uclmanagemententity_detail.html')
