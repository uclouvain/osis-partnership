import json

from django.test import TestCase
from django.urls import reverse

from partnership.tests.factories import (
    PartnershipEntityManagerFactory,
    PartnerFactory, PartnerEntityFactory, PartnershipFactory,
)


class PartnerEntityAutocompleteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = PartnershipEntityManagerFactory().person.user
        cls.url = reverse('partnerships:autocomplete:partner_entity')

        cls.partner = PartnerFactory(organization__name="Université de Nantes")
        cls.entity = PartnerEntityFactory(partner=cls.partner, name="Entity A")
        PartnerEntityFactory(partner=cls.partner, name="Entity B")
        PartnerEntityFactory(name="Other entity")

    def test_partner_entity_autocomplete(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {'q': 'tity'})
        results = response.json()['results']
        self.assertEqual(len(results), 3)

    def test_partner_entity_autocomplete_filter(self):
        self.client.force_login(self.user)
        url = reverse('partnerships:autocomplete:partner_entity_partnerships_filter')

        # No partnership, no partner entity
        response = self.client.get(url)
        self.assertEqual(len(response.json()['results']), 0)

        PartnershipFactory(
            partner_entity=self.entity.entity,
            partner=self.partner,
        )

        # Return entity with partnership
        response = self.client.get(url, {'q': 'tity'})
        results = response.json()['results']
        self.assertEqual(len(results), 1, results)
        self.assertEqual(results[0]['id'], str(self.entity.entity_id))

