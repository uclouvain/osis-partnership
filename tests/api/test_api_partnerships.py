from datetime import date

import freezegun
from django.contrib.gis.geos import Point
from django.test import tag
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from base.models.enums.organization_type import ACADEMIC_PARTNER
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from osis_common.document.xls_build import CONTENT_TYPE_XLS
from partnership.models import (
    AgreementStatus,
    PartnershipConfiguration,
    PartnershipType,
)
from partnership.tests import TestCase
from partnership.tests.factories import (
    FinancingFactory, PartnerFactory,
    PartnershipAgreementFactory, PartnershipFactory,
    PartnershipYearFactory,
    UCLManagementEntityFactory,
    PartnershipSubtypeFactory,
    FundingTypeFactory,
    FundingSourceFactory,
)
from reference.models.continent import Continent
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.domain_isced import DomainIscedFactory

PARTNERSHIP_COUNT = 6


@freezegun.freeze_time('2024-10-24')
class PartnershipApiViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('partnership_api_v1:partnerships')

        AcademicYearFactory.produce_in_future(quantity=3)
        config = PartnershipConfiguration.get_configuration()
        current_academic_year = config.get_current_academic_year_for_api()
        cls.current_academic_year = current_academic_year

        # Continents
        cls.continent = Continent.objects.create(code='AA', name='aaaaa')
        cls.country = CountryFactory(
            name="Albania",
            iso_code='AL',
            continent=cls.continent,
        )
        CountryFactory(continent=cls.continent)
        CountryFactory()

        # Partnerships
        root = EntityVersionFactory(parent=None, entity_type='', acronym="UCL").entity
        sector = EntityVersionFactory(parent=root, acronym="SSH").entity
        entity = EntityVersionFactory(parent=sector, acronym="FIAL").entity
        cls.supervisor_partnership = PersonFactory()
        cls.supervisor_management_entity = PersonFactory()
        cls.funding_type = FundingTypeFactory()
        cls.funding_program = cls.funding_type.program
        cls.funding_source = cls.funding_program.source
        cls.subtype = PartnershipSubtypeFactory()

        cls.partnership = PartnershipFactory(
            ucl_entity=entity,
            supervisor=cls.supervisor_partnership,
            years=[],
            partner__contact_address__country=cls.country,
            partner__contact_address__city="Tirana",
            subtype=cls.subtype,
        )
        cls.partner = cls.partnership.partner_entities.first().organization.partner
        year = PartnershipYearFactory(
            partnership=cls.partnership,
            academic_year=current_academic_year,
            is_smp=True,
            eligible=False,
            funding_source=cls.funding_source,
            funding_program=cls.funding_program,
            funding_type=cls.funding_type,
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
        cls.management_entity = UCLManagementEntityFactory(
            entity=cls.partnership.ucl_entity,
        )

        partnership_without_funding = PartnershipFactory(
            ucl_entity=EntityVersionFactory(parent=sector, acronym="DRT").entity,
            years=[],
        )
        PartnershipYearFactory(
            partnership=partnership_without_funding,
            academic_year=current_academic_year,
        )
        PartnershipAgreementFactory(
            partnership=partnership_without_funding,
            start_academic_year=current_academic_year,
            end_academic_year__year=current_academic_year.year + 1,
            status=AgreementStatus.VALIDATED.name,
        )
        UCLManagementEntityFactory(
            entity=partnership_without_funding.ucl_entity,
            contact_in_person=None,
            contact_out_person=None,
        )

        cls.partnership_2 = PartnershipFactory(
            supervisor=None,
            years__academic_year=current_academic_year,
            partner__contact_address__country__name="Zambia",
            partner__contact_address__country__iso_code="ZM",
            partner__contact_address__city="Lusaka",
            partner__contact_address__location=Point(-15.4166, 28.2822),
        )
        cls.partner_2 = cls.partnership_2.partner_entities.first().organization.partner
        PartnershipAgreementFactory(
            partnership=cls.partnership_2,
            start_academic_year=current_academic_year,
            end_academic_year__year=current_academic_year.year + 1,
            status=AgreementStatus.VALIDATED.name,
        )
        cls.management_entity = UCLManagementEntityFactory(
            entity=cls.partnership_2.ucl_entity,
            academic_responsible=cls.supervisor_management_entity,
            contact_out_person=None,
            contact_in_person=None,
        )
        cls.financing = FinancingFactory(academic_year=current_academic_year)
        cls.financing.countries.add(cls.partner_2.contact_address.country)

        # Other types
        cls.partnership_project = PartnershipFactory(
            partnership_type=PartnershipType.PROJECT.name,
            start_date=date(current_academic_year.year, 1, 1),
            end_date=date(current_academic_year.year, 10, 1),
            partner__contact_address__country__iso_code="ZM",
            partner__contact_address__city="Ndola",
        )
        PartnershipYearFactory(
            partnership=cls.partnership_project,
            academic_year=current_academic_year,
            funding_source=FundingSourceFactory(),
        )

        # Multilateral
        cls.partnership_course = PartnershipFactory(
            partnership_type=PartnershipType.COURSE.name,
            start_date=date(current_academic_year.year, 1, 1),
            end_date=date(current_academic_year.year + 1, 10, 1),
        )
        entity = EntityWithVersionFactory(organization__type=ACADEMIC_PARTNER)
        cls.partnership_course.partner_entities.add(entity)
        PartnerFactory(organization=entity.organization)

        cls.partnership_general = PartnershipFactory(
            partnership_type=PartnershipType.GENERAL.name,
            start_date=date(current_academic_year.year - 1, 1, 1),
            end_date=date(current_academic_year.year + 3, 10, 1),
            partner__contact_address__country__iso_code="ZM",
            partner__contact_address__city="Kabwe",
            partner__contact_address__location=Point(-14.4415250, 28.4441831),
            years=[PartnershipYearFactory(academic_year=current_academic_year)],
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_general,
            start_date=date(current_academic_year.year - 10, 10, 1),
            end_date=date(current_academic_year.year + 7, 10, 1),
            status=AgreementStatus.VALIDATED.name,
        )

        # Some noises - Agreement not validated or not in status validated
        PartnerFactory()
        cls.partnership_without_agreement = PartnershipFactory()
        cls.partnership_not_public = PartnershipFactory(is_public=False)

        cls.partnership_with_agreement_not_validated = PartnershipFactory(
            supervisor=None,
            years__academic_year=current_academic_year,
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_with_agreement_not_validated,
            start_academic_year=current_academic_year,
            end_academic_year__year=current_academic_year.year + 1,
            status=AgreementStatus.WAITING.name,
        )

    @tag('perf')
    def test_get(self):
        with self.assertNumQueriesLessThan(20):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), PARTNERSHIP_COUNT)

    def test_filter_continent(self):
        response = self.client.get(self.url, {'continent': self.continent.name})
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership.uuid))

    def test_filter_country(self):
        response = self.client.get(self.url, {'country': self.country.iso_code})
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership.uuid))

    def test_filter_city(self):
        response = self.client.get(self.url, {
            'city': self.partner.contact_address.city,
        })
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership.uuid))

    def test_filter_partner(self):
        response = self.client.get(self.url, {
            'partner': self.partner.uuid,
        })
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership.uuid))

    def test_filter_ucl_university(self):
        response = self.client.get(self.url, {
            'ucl_entity': self.partnership.ucl_entity.uuid,
            'with_children': True,
        })
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership.uuid))

    def test_filter_education_field(self):
        response = self.client.get(self.url, {
            'education_field': self.education_field.uuid,
        })
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership.uuid))

    def test_filter_mobility_type(self):
        response = self.client.get(self.url + '?mobility_type=student')
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership.uuid))

        response = self.client.get(self.url + '?mobility_type=staff')
        results = response.json()['results']
        self.assertEqual(len(results), 0)

    def test_filter_funding_calculated(self):
        response = self.client.get(self.url,  {
            'funding_source': self.financing.type.program.source_id,
        })
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_2.uuid))

        response = self.client.get(self.url,  {
            'funding_program': self.financing.type.program_id,
        })
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_2.uuid))

        response = self.client.get(self.url,  {
            'funding_type': self.financing.type_id,
        })
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_2.uuid))

    def test_filter_funding_overridden(self):
        response = self.client.get(self.url,  {
            'funding_source': self.funding_source.pk,
        })
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership.uuid))

    def test_filter_bbox(self):
        response = self.client.get(self.url,  {
            'bbox': '-14.7058,27.7625,-16.6072,29.9707',
        })
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_2.uuid))

    def test_status_course_display(self):
        response = self.client.get(self.url,  {
            'type': PartnershipType.COURSE.name,
        })
        results = response.json()['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['uuid'], str(self.partnership_course.uuid))
        self.assertEqual(results[0]['status'], {
            'end_date': str(self.current_academic_year),
            'start_date': str(self.current_academic_year),
            'status': _('status_ongoing'),
        })

    def test_retrieve_case_partnership_with_agreement_validated(self):
        url = reverse(
            'partnership_api_v1:retrieve',
            kwargs={'uuid': self.partnership.uuid},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_retrieve_case_partnership_without_agreement(self):
        url = reverse(
            'partnership_api_v1:retrieve',
            kwargs={'uuid': self.partnership_without_agreement.uuid},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_retrieve_case_partnership_with_agreement_not_validated(self):
        url = reverse(
            'partnership_api_v1:retrieve',
            kwargs={'uuid': self.partnership_with_agreement_not_validated.uuid},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_retrieve_should_not_display_denied_media(self):
        url = reverse(
            'partnership_api_v1:retrieve',
            kwargs={'uuid': self.partnership.uuid},
        )
        response = self.client.get(url)
        self.assertEqual(len(response.json()['bilateral_agreements']), 0)

    @tag('perf')
    def test_export(self):
        url = reverse('partnership_api_v1:export')
        with self.assertNumQueriesLessThan(22):
            response = self.client.get(url)
            self.assertEqual(response['Content-Type'], CONTENT_TYPE_XLS)
