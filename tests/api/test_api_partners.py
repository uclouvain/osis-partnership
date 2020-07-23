from django.urls import reverse

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.person import PersonFactory
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
        cls.country = CountryFactory(continent=cls.continent)
        CountryFactory(continent=cls.continent)
        CountryFactory()

        # Partnerships
        cls.supervisor_partnership = PersonFactory()
        cls.supervisor_management_entity = PersonFactory()

        cls.partnership = PartnershipFactory(
            supervisor=cls.supervisor_partnership,
            years=[],
            partner__contact_address__country=cls.country,
            ucl_entity=EntityFactory(),
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

        partnership = PartnershipFactory(supervisor=None, years=[])
        PartnershipYearFactory(partnership=partnership, academic_year=cls.current_academic_year)
        PartnershipAgreementFactory(
            partnership=partnership,
            start_academic_year=cls.current_academic_year,
            end_academic_year__year=cls.current_academic_year.year + 1,
            status=AgreementStatus.VALIDATED.name,
        )
        cls.management_entity = UCLManagementEntityFactory(
            entity=partnership.ucl_entity,
            academic_responsible=cls.supervisor_management_entity
        )
        cls.financing = FinancingFactory(academic_year=cls.current_academic_year)
        cls.financing.countries.add(partnership.partner.contact_address.country)

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

    def test_get(self):
        with self.assertNumQueriesLessThan(8):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 2)

    def test_ordering_partner(self):
        response = self.client.get(self.url + '?ordering=partner')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 2)

    def test_ordering_country_en(self):
        response = self.client.get(self.url + '?ordering=country_en')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 2)

    def test_ordering_city(self):
        response = self.client.get(self.url + '?ordering=city')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 2)

    def test_ordering_ucl_entity(self):
        response = self.client.get(self.url + '?ordering=ucl_entity')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 2)

    def test_ordering_subject_area(self):
        response = self.client.get(self.url + '?ordering=subject_area')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 2)

    def test_filter_continent(self):
        response = self.client.get(self.url, {
            'continent': self.continent.name,
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)

    def test_filter_country(self):
        response = self.client.get(self.url, {
            'country': self.country.iso_code,
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)

    def test_filter_city(self):
        response = self.client.get(self.url, {
            'city': self.partnership.partner.contact_address.city,
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)

    def test_filter_partner(self):
        response = self.client.get(self.url, {
            'partner': self.partnership.partner.uuid,
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)

    def test_filter_ucl_university(self):
        response = self.client.get(self.url, {
            'ucl_entity': self.partnership.ucl_entity.uuid,
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)

    def test_filter_supervisor(self):
        response = self.client.get(self.url, {
            'supervisor': self.supervisor_partnership.uuid,
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)

    def test_filter_supervisor_in_entity_manager(self):
        response = self.client.get(self.url, {
            'supervisor': self.supervisor_management_entity.uuid,
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)

    def test_filter_education_field(self):
        response = self.client.get(self.url, {
            'education_field': self.education_field.uuid,
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)

    def test_filter_mobility_type(self):
        response = self.client.get(self.url + '?mobility_type=student')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)

    def test_filter_funding(self):
        response = self.client.get(self.url + '?funding=' + self.financing.type.name)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)

    def test_partnerships_count(self):
        partnership = PartnershipFactory()
        PartnershipYearFactory(partnership=partnership, academic_year=self.current_academic_year)
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
        response = self.client.get(self.url + '?partner=' + str(partnership.partner.uuid))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['partnerships_count'], 1)
