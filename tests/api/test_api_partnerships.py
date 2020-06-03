from django.test import TestCase
from django.urls import reverse

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.person import PersonFactory
from partnership.models import AgreementStatus, PartnershipConfiguration
from partnership.tests.factories import (
    FinancingFactory, PartnerFactory,
    PartnershipAgreementFactory, PartnershipFactory,
    PartnershipYearFactory,
    UCLManagementEntityFactory,
)
from reference.models.continent import Continent
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.domain_isced import DomainIscedFactory


class PartnershipApiViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('partnership_api_v1:partnerships:list')

        AcademicYearFactory.produce_in_future(quantity=3)
        current_academic_year = PartnershipConfiguration.get_configuration().get_current_academic_year_for_api()

        # Continents
        cls.continent = Continent.objects.create(code='AA', name='aaaaa')
        cls.country = CountryFactory()
        cls.country.continent = cls.continent
        cls.country.save()
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
            academic_year=current_academic_year,
            is_smp=True,
        )
        cls.education_field = DomainIscedFactory()
        year.education_fields.add(cls.education_field)
        PartnershipAgreementFactory(
            partnership=cls.partnership,
            start_academic_year=current_academic_year,
            end_academic_year__year=current_academic_year.year + 1,
            status=AgreementStatus.VALIDATED.name,
            media__is_visible_in_portal=False,
        )

        partnership = PartnershipFactory(supervisor=None, years=[])
        PartnershipYearFactory(partnership=partnership, academic_year=current_academic_year)
        PartnershipAgreementFactory(
            partnership=partnership,
            start_academic_year=current_academic_year,
            end_academic_year__year=current_academic_year.year + 1,
            status=AgreementStatus.VALIDATED.name,
        )
        cls.management_entity = UCLManagementEntityFactory(
            entity=partnership.ucl_entity,
            academic_responsible=cls.supervisor_management_entity
        )
        cls.financing = FinancingFactory(academic_year=current_academic_year)
        cls.financing.countries.add(partnership.partner.contact_address.country)

        # Some noises - Agreement not validated or not in status validated
        PartnerFactory()
        cls.partnership_without_agreement = PartnershipFactory()
        cls.partnership_not_public = PartnershipFactory(is_public=False)

        cls.partnership_with_agreement_not_validated = PartnershipFactory(supervisor=None, years=[])
        PartnershipYearFactory(
            partnership=cls.partnership_with_agreement_not_validated,
            academic_year=current_academic_year,
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_with_agreement_not_validated,
            start_academic_year=current_academic_year,
            end_academic_year__year=current_academic_year.year + 1,
            status=AgreementStatus.WAITING.name,
        )

    def test_get(self):
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

    def test_ordering_type(self):
        response = self.client.get(self.url + '?ordering=type')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 2)

    def test_ordering_subject_area(self):
        response = self.client.get(self.url + '?ordering=subject_area')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 2)

    def test_filter_continent(self):
        response = self.client.get(self.url + '?continent=' + str(self.continent.name))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)

    def test_filter_country(self):
        response = self.client.get(self.url + '?country=' + str(self.country.iso_code))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)

    def test_filter_city(self):
        response = self.client.get(self.url + '?city=' + str(self.partnership.partner.contact_address.city))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)

    def test_filter_partner(self):
        response = self.client.get(self.url + '?partner=' + str(self.partnership.partner.uuid))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)

    def test_filter_ucl_university(self):
        response = self.client.get(self.url + '?ucl_entity=' + str(self.partnership.ucl_entity.uuid))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)

    def test_filter_supervisor(self):
        response = self.client.get(self.url + '?supervisor=' + str(self.supervisor_partnership.uuid))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)

    def test_filter_supervisor_in_entity_manager(self):
        response = self.client.get(self.url + '?supervisor=' + str(self.supervisor_management_entity.uuid))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)

    def test_filter_education_field(self):
        response = self.client.get(self.url + '?education_field=' + str(self.education_field.uuid))
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

    def test_retrieve_case_partnership_with_agreement_validated(self):
        url = reverse(
            'partnership_api_v1:partnerships:retrieve',
            kwargs={'uuid': self.partnership.uuid},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_retrieve_case_partnership_without_agreement(self):
        url = reverse(
            'partnership_api_v1:partnerships:retrieve',
            kwargs={'uuid': self.partnership_without_agreement.uuid},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_retrieve_case_partnership_with_agreement_not_validated(self):
        url = reverse(
            'partnership_api_v1:partnerships:retrieve',
            kwargs={'uuid': self.partnership_with_agreement_not_validated.uuid},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_retrieve_should_not_display_denied_media(self):
        url = reverse(
            'partnership_api_v1:partnerships:retrieve',
            kwargs={'uuid': self.partnership.uuid},
        )
        response = self.client.get(url)
        self.assertEqual(len(response.json()['bilateral_agreements']), 0)
