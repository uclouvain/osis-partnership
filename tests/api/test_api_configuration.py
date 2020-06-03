from django.test import TestCase
from django.urls import reverse

from base.models.enums.entity_type import FACULTY, SECTOR
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from partnership.models import PartnershipConfiguration
from partnership.tests.factories import (
    FinancingFactory, PartnerFactory,
    PartnershipAgreementFactory, PartnershipFactory, PartnershipYearFactory,
    UCLManagementEntityFactory,
)
from reference.models.continent import Continent
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.domain_isced import DomainIscedFactory


class ConfigurationApiViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('partnership_api_v1:configuration')

        AcademicYearFactory.produce_in_future(quantity=3)
        current_academic_year = PartnershipConfiguration.get_configuration().get_current_academic_year_for_api()

        # Partnerships
        cls.supervisor_partnership = PersonFactory()
        cls.supervisor_management_entity = PersonFactory()

        partnership = PartnershipFactory(supervisor=cls.supervisor_partnership, years=[])
        year = PartnershipYearFactory(
            partnership=partnership,
            academic_year=current_academic_year,
        )
        education_field = DomainIscedFactory(title_en='foo', title_fr='bar')
        year.education_fields.add(education_field)
        PartnershipAgreementFactory(
            partnership=partnership,
            start_academic_year=current_academic_year,
            end_academic_year__year=current_academic_year.year + 1,
        )

        parent = EntityVersionFactory(acronym="SSH", entity_type=SECTOR)
        partnership = PartnershipFactory(
            years=[],
            ucl_entity=EntityVersionFactory(
                acronym="FIAL", entity_type=FACULTY, parent=parent.entity,
            ).entity,
        )
        PartnershipYearFactory(partnership=partnership, academic_year=current_academic_year)
        PartnershipAgreementFactory(
            partnership=partnership,
            start_academic_year=current_academic_year,
            end_academic_year__year=current_academic_year.year + 1,
        )
        UCLManagementEntityFactory(
            entity=partnership.ucl_entity,
            academic_responsible=cls.supervisor_management_entity
        )
        financing = FinancingFactory(academic_year=current_academic_year)
        financing.countries.add(partnership.partner.contact_address.country)

        # Some noises
        PartnerFactory()
        PartnershipFactory()

        # Continents
        continent = Continent.objects.create(code='AA', name='aaaaa')
        CountryFactory(continent=continent)
        CountryFactory(continent=continent)
        CountryFactory()

    def test_continents(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('continents', data)
        self.assertEqual(len(data['continents']), 1)
        self.assertEqual(len(data['continents'][0]['countries']), 2)

    def test_partners(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('partners', data)
        self.assertEqual(len(data['partners']), 2)

    def test_ucl_universities(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('ucl_universities', data)
        self.assertEqual(len(data['ucl_universities']), 2)
        self.assertIn("SSH / FIAL -", data['ucl_universities'][0]['label'])

    def test_education_fields(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('education_fields', data)
        self.assertEqual(len(data['education_fields']), 1)

    def test_get_label_case_language_in_english(self):
        response = self.client.get(self.url, HTTP_ACCEPT_LANGUAGE='en')
        data = response.json()
        self.assertEqual(data['education_fields'][0]['label'], 'foo')

    def test_get_label_case_language_in_french(self):
        response = self.client.get(self.url, HTTP_ACCEPT_LANGUAGE='fr')
        data = response.json()
        self.assertEqual(data['education_fields'][0]['label'], 'bar')

    def test_fundings(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('fundings', data)
        self.assertEqual(len(data['fundings']), 1)
