import json

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from base.models.enums.entity_type import FACULTY, SCHOOL, SECTOR
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory


class YearEntitiesAutocompleteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

        perm = Permission.objects.get(name='can_access_partnerships')
        cls.user.user_permissions.add(perm)

        cls.url = reverse(
            'partnerships:autocomplete:partnership_year_entities')

        # Ucl
        cls.sector = EntityFactory()
        EntityVersionFactory(
            entity=cls.sector,
            entity_type=SECTOR,
            acronym='A',
        )
        cls.ucl_university = EntityFactory()
        EntityVersionFactory(
            entity=cls.ucl_university,
            parent=cls.sector,
            entity_type=FACULTY,
            acronym='AA',
        )
        cls.labo = EntityFactory()
        EntityVersionFactory(
            entity=cls.labo,
            parent=cls.ucl_university,
            entity_type=SCHOOL,
            acronym='AA1',
        )

        cls.labo_2 = EntityFactory()
        EntityVersionFactory(
            entity=cls.labo_2,
            parent=cls.ucl_university,
            entity_type=SCHOOL,
            acronym='AA2',
        )

        cls.ucl_university_2 = EntityFactory()
        EntityVersionFactory(
            entity=cls.ucl_university_2,
            parent=cls.sector,
            entity_type=FACULTY,
            acronym='AB',
        )
        cls.labo_2 = EntityFactory()
        EntityVersionFactory(
            entity=cls.labo_2,
            parent=cls.ucl_university_2,
            entity_type=SCHOOL,
            acronym='AB1',
        )

    def test_year_entities_autocomplete(self):
        self.client.force_login(self.user)

        # No entity, no result
        response = self.client.get(self.url)
        self.assertEqual(len(response.json()['results']), 0)

        def forward(entity, **kwargs):
            return {'forward': json.dumps({'entity': entity.pk}), **kwargs}

        # 2 children on faculty AA
        response = self.client.get(self.url, forward(self.ucl_university))
        self.assertEqual(len(response.json()['results']), 2)

        # 2 sibling on labo AA1
        response = self.client.get(self.url, forward(self.labo))
        self.assertEqual(len(response.json()['results']), 2)

        # 1 child on faculty AB
        response = self.client.get(self.url, forward(self.ucl_university_2))
        self.assertEqual(len(response.json()['results']), 1)

        # self on labo AB1
        response = self.client.get(self.url, forward(self.labo_2))
        self.assertEqual(len(response.json()['results']), 1)

        # with query on AA
        response = self.client.get(self.url, forward(self.labo, q='AA'))
        self.assertEqual(len(response.json()['results']), 2)
