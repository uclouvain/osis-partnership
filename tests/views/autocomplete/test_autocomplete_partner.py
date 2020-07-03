import json
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from partnership.tests.factories import (
    PartnershipEntityManagerFactory, PartnerFactory, PartnerEntityFactory, )


class PartnerAutocompleteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = PartnershipEntityManagerFactory().person.user
        cls.url = reverse('partnerships:autocomplete:partner')

        PartnerFactory(organization__name="University of Albania")
        PartnerFactory(organization__name="Université de Nantes")
        cls.current_partner = PartnerFactory(
            organization__name="Université de Liège",
            dates__end=timezone.now() - timedelta(days=1)
        )
        PartnerFactory(
            organization__name="Université de Namur",
            dates__end=timezone.now() - timedelta(days=1)
        )

    def test_partner_autocomplete_only_actives(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {'q': 'Univ'})
        results = response.json()['results']
        self.assertEqual(len(results), 2)

    def test_partner_autocomplete_with_current_inactive(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {
            'q': 'Univ',
            'forward': json.dumps({
                'partner_pk': self.current_partner.pk,
            }),
        })
        results = response.json()['results']
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['id'], str(self.current_partner.pk))


class PartnerEntityAutocompleteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = PartnershipEntityManagerFactory().person.user
        cls.url = reverse('partnerships:autocomplete:partner_entity')

        cls.partner = PartnerFactory(organization__name="Université de Nantes")
        PartnerEntityFactory(partner=cls.partner, name="Entity A")
        PartnerEntityFactory(partner=cls.partner, name="Entity B")
        PartnerEntityFactory(name="Other entity")

    def test_partner_entity_autocomplete_without_partner(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {'q': 'Ent'})
        results = response.json()['results']
        self.assertEqual(len(results), 0)

    def test_partner_entity_autocomplete(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {
            'q': 'tity',
            'forward': json.dumps({'partner': self.partner.pk}),
        })
        results = response.json()['results']
        self.assertEqual(len(results), 2)
