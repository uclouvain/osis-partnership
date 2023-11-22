from django.contrib.gis.geos import Point
from django.test import tag
from django.urls import reverse
from rest_framework.test import APIClient

from base.models.enums import organization_type
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.entity_version_address import MainRootEntityVersionAddressFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory
from partnership.models import AgreementStatus, PartnershipConfiguration
from partnership.tests import TestCase
from partnership.tests.factories import (
    FinancingFactory, PartnerFactory,
    PartnershipAgreementFactory, PartnershipFactory,
    PartnershipYearFactory,
    UCLManagementEntityFactory,
)
from reference.models.continent import Continent
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.domain_isced import DomainIscedFactory


class PartnersApiViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('partnership_api_v1:partners')

        AcademicYearFactory.produce_in_future(quantity=3)
        cls.current_academic_year = PartnershipConfiguration.get_configuration().get_current_academic_year_for_api()

        # Continents
        cls.continent = Continent.objects.create(code='AA', name='aaaaa')
        cls.country = CountryFactory(
            continent=cls.continent,
            iso_code="AL",
            name="Albania",
        )
        CountryFactory(continent=cls.continent)
        CountryFactory()

        # Partnerships
        cls.supervisor_partnership = PersonFactory()
        cls.supervisor_management_entity = PersonFactory()

        cls.partnership = PartnershipFactory(
            supervisor=cls.supervisor_partnership,
            years=[],
            partner_entity__organization__name="University of Albania",
            partner__contact_address__country=cls.country,
            partner__contact_address__city="Tirana",
            partner__contact_address__location=Point(
                19.8186, 41.3275
            ),
        )
        year = PartnershipYearFactory(
            partnership=cls.partnership,
            academic_year=cls.current_academic_year,
            is_smp=True,
        )
        cls.education_field = DomainIscedFactory()
        year.education_fields.add(cls.education_field)
        PartnershipAgreementFactory(
            partnership=cls.partnership,
            start_academic_year=cls.current_academic_year,
            end_academic_year__year=cls.current_academic_year.year + 1,
            status=AgreementStatus.VALIDATED.name,
        )

        cls.partnership_2 = PartnershipFactory(
            supervisor=None,
            years__academic_year=cls.current_academic_year,
            partner_entity__organization__name="Art school",
            partner__contact_address__country__iso_code="ZM",
            partner__contact_address__country__name="Zambia",
            partner__contact_address__city="Lusaka",
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_2,
            start_academic_year=cls.current_academic_year,
            end_academic_year__year=cls.current_academic_year.year + 1,
            status=AgreementStatus.VALIDATED.name,
        )
        cls.management_entity = UCLManagementEntityFactory(
            entity=cls.partnership_2.ucl_entity,
            academic_responsible=cls.supervisor_management_entity
        )
        cls.financing = FinancingFactory(academic_year=cls.current_academic_year)
        partner = cls.partnership_2.partner_entities.first().organization.partner
        cls.financing.countries.add(partner.contact_address.country)

        cls.partner_uuid = cls.partnership.partner_entities.first().organization.partner.uuid
        cls.partner_2_uuid = cls.partnership_2.partner_entities.first().organization.partner.uuid

        # Some noises
        PartnerFactory()
        PartnershipFactory()
        PartnershipFactory(
            supervisor=cls.supervisor_partnership,
            years=[],
            is_public=False,
            partner__contact_address__country=cls.country,
            ucl_entity=EntityFactory(),
        )

    @tag('perf')
    def test_get(self):
        with self.assertNumQueriesLessThan(8):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)

    def test_ordering_partner(self):
        response = self.client.get(self.url + '?ordering=partner')
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['uuid'], str(self.partner_2_uuid))

    def test_ordering_country_en(self):
        response = self.client.get(self.url + '?ordering=country_en')
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['uuid'], str(self.partner_uuid))

    def test_ordering_city(self):
        response = self.client.get(self.url + '?ordering=city')
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['uuid'], str(self.partner_2_uuid))

    def test_filter_continent(self):
        response = self.client.get(self.url, {
            'continent': self.continent.name,
        })
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['uuid'], str(self.partner_uuid))

    def test_filter_country(self):
        response = self.client.get(self.url, {
            'country': self.country.iso_code,
        })
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['uuid'], str(self.partner_uuid))

    def test_filter_city(self):
        response = self.client.get(self.url, {'city': "Lusaka"})
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['uuid'], str(self.partner_2_uuid))

    def test_filter_partner(self):
        response = self.client.get(self.url, {
            'partner': self.partner_uuid,
        })
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['uuid'], str(self.partner_uuid))

    def test_filter_ucl_university(self):
        response = self.client.get(self.url, {
            'ucl_entity': self.partnership.ucl_entity.uuid,
        })
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['uuid'], str(self.partner_uuid))

    def test_filter_education_field(self):
        response = self.client.get(self.url, {
            'education_field': self.education_field.uuid,
        })
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['uuid'], str(self.partner_uuid))

    def test_filter_mobility_type(self):
        response = self.client.get(self.url + '?mobility_type=student')
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['uuid'], str(self.partner_uuid))

        response = self.client.get(self.url + '?mobility_type=staff')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 0)

    def test_filter_funding(self):
        response = self.client.get(self.url, {
            'funding_type':  self.financing.type_id,
        })
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['uuid'], str(self.partner_2_uuid))

    def test_partnerships_count(self):
        partnership = PartnershipFactory(
            years__academic_year=self.current_academic_year,
        )
        PartnershipAgreementFactory(
            partnership=partnership,
            start_academic_year=self.current_academic_year,
            end_academic_year__year=self.current_academic_year.year + 1,
            status=AgreementStatus.WAITING.name,
        )
        PartnershipAgreementFactory(
            partnership=partnership,
            start_academic_year=self.current_academic_year,
            end_academic_year__year=self.current_academic_year.year + 5,
            status=AgreementStatus.VALIDATED.name,
        )
        partner = partnership.partner_entities.first().organization.partner
        response = self.client.get(self.url + '?partner=' + str(partner.uuid))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['partnerships_count'], 1)


class InternshipPartnerListApiViewTest(TestCase):
    client_class = APIClient

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('partnership_api_v1:internship_partners')
        cls.partner = PartnerFactory(contact_address__location='SRID=4326;POINT(12 13)')
        cls.country = CountryFactory()
        person = PersonFactory()
        cls.user = person.user

    def setUp(self) -> None:
        self.client.force_authenticate(user=self.user)

    def test_post(self):
        data = {
            'name': 'foobar',
            'organisation_identifier': 'weewf',
            'size': '<250',
            'is_public': 'false',
            'is_nonprofit': 'true',
            'type': "ACADEMIC_PARTNER",
            'website': 'http://example.org/',
            'street_number': '2',
            'street': 'rue machin',
            'postal_code': '12345',
            'city': 'truc',
            'country': self.country.iso_code,
            'latitude': 42.123,
            'longitude': -12.5,
        }
        response = self.client.post(self.url, data)
        data = response.json()
        self.assertEqual(response.status_code, 201, data)
        self.assertEqual(data['name'], 'foobar')
        self.assertFalse(data['is_public'])
        self.assertTrue(data['is_nonprofit'])

    def test_post_minimal(self):
        data = {
            'name': 'foobar',
            'organisation_identifier': 'weewf',
            'size': '<250',
            'is_public': 'false',
            'is_nonprofit': 'true',
            'type': "ACADEMIC_PARTNER",
            'website': 'http://example.org/',
            'street': 'rue machin',
            'city': 'truc',
            'country': self.country.iso_code,
        }
        response = self.client.post(self.url, data)
        data = response.json()
        self.assertEqual(response.status_code, 201, data)
        self.assertEqual(data['name'], 'foobar')
        self.assertFalse(data['is_public'])
        self.assertTrue(data['is_nonprofit'])

    def test_get_no_filter(self):
        response = self.client.get(self.url)
        data = response.json()
        self.assertEqual(response.status_code, 400)

    def test_get_incorrect_filter(self):
        response = self.client.get(self.url + '?from_date=foo')
        data = response.json()
        self.assertEqual(response.status_code, 400)

    def test_get(self):
        response = self.client.get(self.url + '?from_date=1831-07-21')
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['name'], self.partner.organization.name)

    def test_get_future(self):
        response = self.client.get(self.url + '?from_date=2192-07-21')
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data['results']), 0)


class InternshipPartnerDetailApiViewTest(TestCase):
    client_class = APIClient

    @classmethod
    def setUpTestData(cls):
        cls.partner = PartnerFactory(contact_address__location='SRID=4326;POINT(12 13)')
        cls.url = reverse('partnership_api_v1:internship_partner', kwargs={'uuid': str(cls.partner.uuid)})
        cls.country = CountryFactory()
        person = PersonFactory()
        cls.user = person.user

    def setUp(self) -> None:
        self.client.force_authenticate(self.user)

    def test_get(self):
        response = self.client.get(self.url)
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['name'], self.partner.organization.name)


class DeclareOrganizationAsInternshipPartnerApiViewTest(TestCase):
    client_class = APIClient

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('partnership_api_v1:declare_organization_as_internship_partner')
        cls.existing_organization = OrganizationFactory(
            name="Organization existante",
            type=organization_type.EMBASSY,
        )
        cls.root_entity_version = EntityVersionFactory(
            parent=None,
            title=cls.existing_organization.name,
            entity__organization=cls.existing_organization,
        )
        MainRootEntityVersionAddressFactory(entity_version=cls.root_entity_version)

        cls.existing_partner = PartnerFactory()
        person = PersonFactory()
        cls.user = person.user

    def setUp(self) -> None:
        self.client.force_authenticate(user=self.user)

    def test_post_with_existing_organization(self):
        data = {
            'organization_uuid': self.existing_organization.uuid,
            'organisation_identifier': 'weewf',
            'size': '<250',
            'is_public': 'false',
            'is_nonprofit': 'true',
        }
        response = self.client.post(self.url, data)
        data = response.json()
        self.assertEqual(response.status_code, 201, data)

        self.assertEqual(data['name'], self.existing_organization.name)
        self.assertFalse(data['is_public'])
        self.assertTrue(data['is_nonprofit'])

    def test_post_no_existing_organization(self):
        data = {
            'organization_uuid': 'cec580dd-595a-436b-94fe-5ae0d9885fc9',
            'organisation_identifier': 'weewf',
            'size': '<250',
            'is_public': 'false',
            'is_nonprofit': 'true',
        }
        response = self.client.post(self.url, data)
        data = response.json()
        self.assertEqual(response.status_code, 400, data)

    def test_post_existing_organization_already_partner(self):
        data = {
            'organization_uuid': self.existing_partner.organization.uuid,
            'organisation_identifier': 'weewf',
            'size': '<250',
            'is_public': 'false',
            'is_nonprofit': 'true',
        }
        response = self.client.post(self.url, data)
        data = response.json()
        self.assertEqual(response.status_code, 400, data)
        self.assertEqual(data['detail'], "This organization is already declared as partner")
        self.assertEqual(data['partner_uuid'], str(self.existing_partner.uuid))
