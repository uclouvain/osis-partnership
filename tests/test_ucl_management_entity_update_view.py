from django.test import TestCase
from django.urls import reverse
from base.tests.factories.user import UserFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.models.enums.entity_type import FACULTY
from partnership.tests.factories import UCLManagementEntityFactory
from django.urls import reverse


class UCLManagementEntityUpdateViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.ucl_management_entity = UCLManagementEntityFactory()
        cls.url = reverse(
            "partnerships:ucl_management_entities:update",
            kwargs={'pk': cls.ucl_management_entity.pk},
        )

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
        self.assertTemplateNotUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_update.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_view_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed('partnerships/ucl_management_entities/uclmanagemententity_update.html')

    def test_post(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/ucl_management_entity/uclmanagemententity_detail.html')
        self.assertEqual(self.ucl_management_entity.academic_responsible, self.data['academic_responsible'])
        self.assertEqual(self.ucl_management_entity.administrative_responsible, self.data['administrative_responsible'])
        self.assertEqual(self.ucl_management_entity.contact_in_email, self.data['contact_in_email'])
        self.assertEqual(self.ucl_management_entity.contact_in_person, self.data['contact_in_person'])
        self.assertEqual(self.ucl_management_entity.contact_in_url, self.data['contact_in_url'])
        self.assertEqual(self.ucl_management_entity.contact_out_email, self.data['contact_out_email'])
        self.assertEqual(self.ucl_management_entity.contact_out_person, self.data['contact_out_person'])
        self.assertEqual(self.ucl_management_entity.contact_out_url, self.data['contact_out_url'])
        self.assertEqual(self.ucl_management_entity.faculty, self.data['faculty'])
        self.assertEqual(self.ucl_management_entity.entity, self.data['entity'])
