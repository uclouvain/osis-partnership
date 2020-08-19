import json

from django.test import TestCase
from django.urls import reverse

from partnership.models import PartnershipType
from partnership.tests.factories import (
    PartnershipEntityManagerFactory, PartnershipSubtypeFactory,
)


class SubtypeAutocompleteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = PartnershipEntityManagerFactory().person.user
        cls.url = reverse('partnerships:autocomplete:subtype')

        cls.subtype1 = PartnershipSubtypeFactory(types=[
            PartnershipType.MOBILITY.name,
            PartnershipType.GENERAL.name,
        ])
        cls.subtype2 = PartnershipSubtypeFactory(types=[
            PartnershipType.COURSE.name,
            PartnershipType.DOCTORATE.name,
        ])

    def test_subtype_authenticated(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)
        results = response.json()['results']
        self.assertEqual(len(results), 0)

        response = self.client.get(
            self.url,
            data={'forward': json.dumps({'partnership_type': 'GENERAL'})},
        )
        results = response.json()['results']
        labels = [result['text'] for result in results]
        self.assertIn(str(self.subtype1), labels)
        self.assertNotIn(str(self.subtype2), labels)
