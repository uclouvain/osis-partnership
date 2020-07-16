from django.test import TestCase
from django.urls import reverse

from partnership.models import FundingSource, FundingProgram
from partnership.tests.factories import (
    PartnershipEntityManagerFactory,
    FundingTypeFactory,
)


class FundingAutocompleteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = PartnershipEntityManagerFactory().person.user
        cls.url = reverse('partnerships:autocomplete:funding')

        # Delete default objects made by migration
        FundingSource.objects.all().delete()
        FundingProgram.objects.all().delete()

        FundingTypeFactory(
            program__source__name="Ipsum", program__name="Lorem", name="Foobar"
        )
        FundingTypeFactory(
            program__source__name="Foo", program__name="Bar", name="Baz",
        )

    def test_funding_autocomplete(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        results = response.json()['results']
        self.assertEqual(len(results), 6)
        self.assertEqual(results[0]['text'], "Foo")

        response = self.client.get(self.url, {'q': 'bar'})
        results = response.json()['results']
        # should retrieve lorem>ipsum>foobar, foo>bar, type foo>bar>baz
        self.assertEqual(len(results), 3, results)
        self.assertEqual(results[0]['text'], "Foo > Bar")
        self.assertEqual(results[1]['text'], "Foo > Bar > Baz")

        response = self.client.get(self.url, {'q': 'lorem'})
        results = response.json()['results']
        self.assertEqual(len(results), 2)  # program and type
        self.assertEqual(results[0]['text'], "Ipsum > Lorem")
