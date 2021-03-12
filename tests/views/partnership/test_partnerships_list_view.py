from datetime import date

from django.shortcuts import resolve_url
from django.test import tag

from base.models.academic_year import AcademicYear
from base.models.enums.entity_type import FACULTY, SECTOR
from base.models.enums.organization_type import RESEARCH_CENTER
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory as BaseEducationGroupYearFactory
from base.tests.factories.entity_version import EntityVersionFactory as BaseEntityVersionFactory
from base.tests.factories.user import UserFactory
from osis_common.document.xls_build import CONTENT_TYPE_XLS
from partnership.forms import PartnershipFilterForm
from partnership.models import AgreementStatus, PartnershipType
from partnership.models.enums.filter import DateFilterType
from partnership.tests import TestCase
from partnership.tests.factories import (
    PartnerEntityFactory,
    PartnerFactory,
    PartnerTagFactory,
    PartnershipAgreementFactory as BasePartnershipAgreementFactory,
    PartnershipEntityManagerFactory,
    PartnershipFactory as BasePartnershipFactory,
    PartnershipTagFactory,
    PartnershipYearEducationLevelFactory,
    PartnershipYearFactory,
    FinancingFactory,
    MediaFactory,
    FundingTypeFactory,
)
from partnership.tests.factories import PartnershipSubtypeFactory
from reference.models.continent import Continent
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.domain_isced import DomainIscedFactory


class PartnershipsListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        class EntityVersionFactory(BaseEntityVersionFactory):
            entity__organization = None

        root = EntityVersionFactory(parent=None).entity

        class EducationGroupYearFactory(BaseEducationGroupYearFactory):
            management_entity = None
            administration_entity = None
            enrollment_campus = None

        class PartnershipAgreementFactory(BasePartnershipAgreementFactory):
            media = MediaFactory()

        class PartnershipFactory(BasePartnershipFactory):
            ucl_entity = EntityVersionFactory(parent=root).entity

        cls.partnership_first_name = PartnershipFactory(
            partner_entity__organization__name='Albania School',
        )

        # ucl_university
        parent = EntityVersionFactory(
            acronym='AAA',
            entity_type=SECTOR,
            parent=root,
        ).entity
        cls.ucl_university = EntityVersionFactory(
            parent=parent,
            entity_type=FACULTY,
            acronym='ZZZ',
        ).entity
        cls.partnership_ucl_university = PartnershipFactory(
            ucl_entity=cls.ucl_university
        )

        # ucl_university_labo
        cls.ucl_university_labo = EntityVersionFactory(
            parent=cls.ucl_university,
            acronym='AAA',
        ).entity
        cls.partnership_ucl_university_labo = PartnershipFactory(
            ucl_entity=cls.ucl_university_labo
        )

        # university_offer
        cls.university_offer = EducationGroupYearFactory()
        cls.partnership_university_offer = PartnershipFactory(years=[])
        partnership_year = PartnershipYearFactory(
            partnership=cls.partnership_university_offer,
            academic_year__year=2101,
        )
        partnership_year.offers.add(cls.university_offer)

        # partner
        cls.partner = PartnerFactory(
            contact_address__city='Tirana',
            contact_address__country__name='Albania',
            contact_address__country__iso_code='AL',
        )
        cls.partnership_partner = PartnershipFactory(
            partner_entity__organization=cls.partner.organization,
        )
        cls.partnership_partner_type = BasePartnershipFactory(
            ucl_entity=PartnershipFactory.ucl_entity,
            partner_entity__organization__type=RESEARCH_CENTER,
        )

        # partner_entity
        cls.partnership_partner_entity = PartnershipFactory()
        cls.partner_entity = cls.partnership_partner_entity.partner_entity

        # use_egracons
        cls.partnership_use_egracons = BasePartnershipFactory(
            ucl_entity=PartnershipFactory.ucl_entity,
            partner__use_egracons=True,
        )

        # city
        cls.partnership_city = BasePartnershipFactory(
            ucl_entity=PartnershipFactory.ucl_entity,
            partner__contact_address__city='Berat',
            partner__contact_address__country__iso_code='AL',
        )

        # country
        cls.country = CountryFactory()
        partner_country = PartnerFactory(contact_address__country=cls.country)
        cls.partnership_country = PartnershipFactory(
            partner_entity=partner_country.organization.entity_set.first()
        )

        # continent
        cls.continent = Continent.objects.create(code='fo', name='foo')
        country_continent = CountryFactory(
            iso_code='FO',  # This is needed to prevent caching
            continent=cls.continent,
        )
        partner_continent = PartnerFactory(contact_address__country=country_continent)
        cls.partnership_continent = PartnershipFactory(
            partner_entity=partner_continent.organization.entity_set.first(),
        )

        # partner_tags
        cls.partner_tag = PartnerTagFactory()
        partner_tag = PartnerFactory(tags=[cls.partner_tag])
        cls.partnership_partner_tags = PartnershipFactory(
            partner_entity_id=partner_tag.organization.entity_set.first().pk,
        )

        # education_field
        cls.education_field = DomainIscedFactory()
        partnership_year = PartnershipYearFactory(academic_year__year=2120)
        partnership_year.education_fields.add(cls.education_field)
        cls.partnership_education_field = partnership_year.partnership
        partnership_year.offers.add(EducationGroupYearFactory())

        # education_level
        cls.education_level = PartnershipYearEducationLevelFactory()
        partnership_year = PartnershipYearFactory(academic_year__year=2120)
        partnership_year.education_levels.add(cls.education_level)
        cls.partnership_education_level = partnership_year.partnership

        # is_sms
        cls.partnership_is_sms = PartnershipYearFactory(
            is_sms=True,
            academic_year__year=2150,
        ).partnership
        # is_smp
        cls.partnership_is_smp = PartnershipYearFactory(
            is_smp=True,
            academic_year__year=2151,
        ).partnership
        # is_sta
        cls.partnership_is_sta = PartnershipYearFactory(
            is_sta=True,
            academic_year__year=2152,
        ).partnership
        # is_stt
        cls.partnership_is_stt = PartnershipYearFactory(
            is_stt=True,
            academic_year__year=2153,
        ).partnership

        # partnership_type
        cls.partnership_general = PartnershipFactory(
            partnership_type=PartnershipType.GENERAL.name,
            years__academic_year__year=2154,
            end_date=date(2020, 7, 1),
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_general,
            status=AgreementStatus.VALIDATED.name,
        )

        cls.partnership_course = PartnershipFactory(
            partnership_type=PartnershipType.COURSE.name,
            years__academic_year__year=2154,
        )

        # tags
        cls.tag = PartnershipTagFactory()
        cls.partnership_tag = PartnershipFactory(tags=[cls.tag])

        # comment
        cls.partnership_comment = PartnershipFactory(comment='foobar')

        # partnership_in
        cls.partnership_partnership_in = PartnershipFactory()
        PartnershipAgreementFactory(
            partnership=cls.partnership_partnership_in,
            start_academic_year__year=2115,
            end_academic_year__year=2116,
        )
        # partnership_ending_in
        cls.partnership_partnership_ending_in = PartnershipFactory()
        PartnershipAgreementFactory(
            partnership=cls.partnership_partnership_ending_in,
            start_academic_year__year=2108,
            end_academic_year__year=2109,
        )
        # partnership_valid_in
        cls.partnership_partnership_valid_in = PartnershipFactory()
        PartnershipAgreementFactory(
            partnership=cls.partnership_partnership_valid_in,
            status=AgreementStatus.VALIDATED.name,
            start_academic_year__year=2117,
            end_academic_year__year=2118,
        )
        # partnership_ending_in
        cls.partnership_partnership_not_valid_in = PartnershipFactory()
        PartnershipAgreementFactory(
            partnership=cls.partnership_partnership_not_valid_in,
            start_academic_year__year=2119,
            end_academic_year__year=2120,
        )
        # partnership_no_agreement_in
        cls.partnership_partnership_no_agreement_in = PartnershipFactory(
            years__academic_year__year=2180,
        )
        # All filters
        cls.country_all_filters = CountryFactory(
            iso_code='BA',  # This is needed to prevent caching
            continent=Continent.objects.create(code='ba', name='bar'),
        )
        sector = EntityVersionFactory(
            acronym='ZZZ',
            entity_type=SECTOR,
            parent=root,
        )
        faculty = EntityVersionFactory(
            acronym='ZZZ',
            entity_type=FACULTY,
            parent=sector.entity,
        )
        labo = EntityVersionFactory(
            acronym='ZZZ',
            parent=faculty.entity,
        )
        cls.all_partner_tag = PartnerTagFactory()
        cls.partner_all_filters = PartnerFactory(
            contact_address__city='all_filters',
            contact_address__country=cls.country_all_filters,
            tags=[cls.all_partner_tag],
        )
        partner_entity = PartnerEntityFactory(
            partner=cls.partner_all_filters,
        )
        cls.partnership_all_filters = PartnershipFactory(
            ucl_entity=labo.entity,
            comment='all_filters',
            partner_entity_id=partner_entity.entity_id,
            years=[],
            start_date=date(2160, 9, 1),
            end_date=date(2161, 6, 30),
        )
        partnership_year = PartnershipYearFactory(
            partnership=cls.partnership_all_filters,
            is_sms=False,
            is_smp=False,
            is_sta=False,
            is_stt=False,
            academic_year__year=2160,
        )
        partnership_year.offers.add(EducationGroupYearFactory())
        cls.all_education_field = DomainIscedFactory()
        partnership_year.education_fields.add(cls.all_education_field)
        cls.all_education_level = PartnershipYearEducationLevelFactory()
        partnership_year.education_levels.add(cls.all_education_level)
        cls.all_partnership_tag = PartnershipTagFactory()
        cls.partnership_all_filters.tags.add(cls.all_partnership_tag)
        PartnershipAgreementFactory(
            partnership=cls.partnership_all_filters,
            start_academic_year__year=2125,
            end_academic_year__year=2127,
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_all_filters,
            status=AgreementStatus.VALIDATED.name,
            start_academic_year__year=2127,
            end_academic_year__year=2129,
        )
        AcademicYearFactory(year=2126)

        cls.user = UserFactory()
        PartnershipEntityManagerFactory(person__user=cls.user, scopes=[
            PartnershipType.GENERAL.name,
            PartnershipType.MOBILITY.name,
        ])
        cls.url = resolve_url('partnerships:list')

    def test_get_list_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnership/partnership_list.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_list_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.context['object_list'].count(), 28)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')

    @tag('perf')
    def test_get_num_queries_serializer(self):
        self.client.force_login(self.user)
        with self.assertNumQueriesLessThan(12):
            self.client.get(self.url, HTTP_ACCEPT='application/json')

    def test_get_list_ordering(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?ordering=partner', HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(results[0]['uuid'], str(self.partnership_first_name.uuid))

    def test_get_list_ordering_country(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?ordering=country', HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(results[0]['uuid'], str(self.partnership_city.uuid))
        self.assertEqual(results[1]['uuid'], str(self.partnership_partner.uuid))

    def test_get_list_ordering_ucl(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?ordering=ucl', HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(results[0]['uuid'], str(self.partnership_ucl_university.uuid))
        self.assertEqual(results[1]['uuid'], str(self.partnership_ucl_university_labo.uuid))

    def test_filter_ucl_university(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {
            'ucl_entity': self.ucl_university.pk,
            'ucl_entity_with_child': True,
            'ordering': 'ucl',
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['uuid'], str(self.partnership_ucl_university.uuid))
        self.assertEqual(results[1]['uuid'], str(self.partnership_ucl_university_labo.uuid))

        response = self.client.get(self.url, {
            'ucl_entity': self.ucl_university.pk,
            'ucl_entity_with_child': False,
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_ucl_university.uuid))

    def test_filter_ucl_university_labo(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {
            'ucl_entity': self.ucl_university_labo.pk
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_ucl_university_labo.uuid))

    def test_filter_university_offers(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {
            'university_offer': self.university_offer.pk,
        }, HTTP_ACCEPT='application/json')
        json = response.json()
        uuids = [o['uuid'] for o in json['object_list']]
        self.assertIn(str(self.partnership_university_offer.uuid), uuids)
        # Include partnerships with offers at None (28 total - 2 with other offers)
        self.assertEqual(json['total'], 26)

    def test_filter_partner_entity(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {
            'partner_entity': self.partner_entity.pk,
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_partner_entity.uuid))
        
    def test_filter_use_egracons(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {
            'use_egracons': True
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_use_egracons.uuid))

    def test_filter_partner_type(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {
            'partner_type': RESEARCH_CENTER,
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_partner_type.uuid))

    def test_filter_city(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {
            'city': 'Berat',
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_city.uuid))

    def test_filter_country(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {
            'country': self.country.pk,
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_country.uuid))

    def test_filter_continent(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {
            'continent': self.continent.pk,
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_continent.uuid))

    def test_filter_partner_tags(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {
            'partner_tags': self.partner_tag.pk,
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_partner_tags.uuid))

    def test_filter_education_field(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {
            'education_field': self.education_field.pk,
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_education_field.uuid))

    def test_filter_education_level(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {
            'education_level': self.education_level.pk,
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_education_level.uuid))

    def test_filter_is_sms(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {
            'is_sms': True,
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_is_sms.uuid))

    def test_filter_is_smp(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {
            'is_smp': True,
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_is_smp.uuid))

    def test_filter_is_sta(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {
            'is_sta': True,
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_is_sta.uuid))

    def test_filter_is_stt(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {
            'is_stt': True,
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_is_stt.uuid))

    def test_filter_partnership_type(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {
            'partnership_type': PartnershipType.GENERAL.name,
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_general.uuid))
        self.assertEqual(results[0]['validity_end'], "01/07/2020")

        response = self.client.get(self.url, {
            'partnership_type': PartnershipType.COURSE.name,
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_course.uuid))
        self.assertEqual(results[0]['validity_end'], "2154-55")

    def test_filter_tags(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {
            'tags': self.tag.pk,
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_tag.uuid))

    def test_filter_comment(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {
            'comment': 'foo',
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_comment.uuid))

    def test_filter_partnership_in(self):
        self.client.force_login(self.user)
        academic_year = self.partnership_partnership_in.agreements.first().start_academic_year_id
        response = self.client.get(self.url, {
            'partnership_in': academic_year,
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_partnership_in.uuid))

    def test_filter_partnership_ending_in(self):
        self.client.force_login(self.user)
        academic_year = self.partnership_partnership_ending_in.agreements.first().end_academic_year_id
        response = self.client.get(self.url, {
            'partnership_ending_in': academic_year,
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_partnership_ending_in.uuid))

    def test_filter_partnership_valid_in(self):
        self.client.force_login(self.user)
        academic_year = self.partnership_partnership_valid_in.agreements.first().start_academic_year_id
        response = self.client.get(self.url, {
            'partnership_valid_in': academic_year,
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_partnership_valid_in.uuid))
        self.assertEqual(results[0]['validity_end'], "2118-19")

    def test_filter_partnership_not_valid_in(self):
        self.client.force_login(self.user)
        academic_year = self.partnership_partnership_not_valid_in.agreements.first().start_academic_year_id
        response = self.client.get(self.url, {
            'partnership_not_valid_in': academic_year,
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_partnership_not_valid_in.uuid))
        self.assertIsNone(results[0]['validity_end'])

    def test_filter_partnership_no_agreements_in(self):
        self.client.force_login(self.user)
        academic_year = self.partnership_partnership_no_agreement_in.years.first().academic_year_id
        response = self.client.get(self.url, {
            'partnership_with_no_agreements_in': academic_year,
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_partnership_no_agreement_in.uuid))

    def test_filter_special_dates_errors(self):
        form = PartnershipFilterForm({
            'partnership_date_type': DateFilterType.ONGOING.name,
        }, user=self.user)
        self.assertIn('partnership_date_from', form.errors)

        form = PartnershipFilterForm({
            'partnership_date_type': DateFilterType.ONGOING.name,
            'partnership_date_from': '10/09/2020',
            'partnership_date_to': '01/09/2020',
        }, user=self.user)
        self.assertIn('partnership_date_to', form.errors)

        form = PartnershipFilterForm({
            'partnership_date_type': DateFilterType.ONGOING.name,
            'partnership_date_from': '01/09/2020',
            'partnership_date_to': '10/09/2020',
        }, user=self.user)
        self.assertFalse(form.errors)

    def test_filter_special_dates_ongoing(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {
            'partnership_date_type': DateFilterType.ONGOING.name,
            'partnership_date_from': '25/10/2160',
            'partnership_date_to': '25/10/2160',
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_all_filters.uuid))

        response = self.client.get(self.url, {
            'partnership_date_type': DateFilterType.ONGOING.name,
            'partnership_date_from': '25/10/2160',
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_all_filters.uuid))

    def test_filter_special_dates_stopping(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {
            'partnership_date_type': DateFilterType.STOPPING.name,
            'partnership_date_from': '25/06/2020',
            'partnership_date_to': '05/07/2020',
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_general.uuid))

    def test_with_all_filters(self):
        self.client.force_login(self.user)
        first_year = self.partnership_all_filters.years.filter(offers__isnull=False).first()
        data = {
            'ucl_entity': self.partnership_all_filters.ucl_entity_id,
            'university_offers': first_year.offers.first().pk,
            'use_egracons': False,
            'partner_entity': self.partnership_all_filters.partner_entity_id,
            'city': 'all_filters',
            'country': self.country_all_filters.pk,
            'continent': self.country_all_filters.continent_id,
            'partner_tags': self.all_partner_tag.pk,
            'education_field': self.all_education_field.pk,
            'education_level': self.all_education_level.pk,
            'is_sms': False,
            'is_smp': False,
            'is_sta': False,
            'is_stt': False,
            'tags': self.all_partnership_tag.pk,
            'comment': 'all_filters',
            'partnership_in': AcademicYear.objects.get(year=2125).pk,
            'partnership_ending_in': AcademicYear.objects.get(year=2129).pk,
            'partnership_valid_in': AcademicYear.objects.get(year=2127).pk,
            'partnership_not_valid_in': AcademicYear.objects.get(year=2126).pk,
        }
        response = self.client.get(self.url, data, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_all_filters.uuid))

    @tag('perf')
    def test_export_all(self):
        self.client.force_login(self.user)

        # We need more precise objects (on the correct academic year)
        year = AcademicYearFactory(year=2136)
        partnership1 = BasePartnershipFactory(
            years=[],
            partner__contact_address=True,
        )
        partnership_year = PartnershipYearFactory(
            partnership=partnership1,
            academic_year=year,
        )
        partnership_year.education_levels.add(
            PartnershipYearEducationLevelFactory(),
            PartnershipYearEducationLevelFactory(),
        )
        partnership1.tags.add(PartnershipTagFactory(), PartnershipTagFactory())
        BasePartnershipAgreementFactory(
            partnership=partnership1,
            status=AgreementStatus.VALIDATED.name,
            start_academic_year=year,
            end_academic_year__year=2137,
        )
        financing = FinancingFactory(academic_year=year)
        financing.countries.add(partnership1.partner.contact_address.country)

        partnership2 = BasePartnershipFactory(
            partnership_type=PartnershipType.PROJECT.name,
            years__academic_year=year,
            subtype=PartnershipSubtypeFactory(),
            years__funding_type=FundingTypeFactory(),
        )
        BasePartnershipAgreementFactory(
            partnership=partnership2,
            status=AgreementStatus.VALIDATED.name,
            start_academic_year=year,
            end_academic_year__year=2137,
        )

        url = resolve_url('partnerships:export', academic_year_pk=year.pk)
        with self.assertNumQueriesLessThan(26):
            response = self.client.get(url)
            self.assertEqual(response['Content-Type'], CONTENT_TYPE_XLS)
        self.assertTemplateNotUsed(response, 'partnerships/partnership/partnership_list.html')
