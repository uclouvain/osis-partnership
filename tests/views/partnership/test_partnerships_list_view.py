from datetime import date

from django.shortcuts import resolve_url

from base.models.academic_year import AcademicYear
from base.models.enums.entity_type import FACULTY, SECTOR
from base.models.enums.organization_type import ACADEMIC_PARTNER
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory as BaseEducationGroupYearFactory
from base.tests.factories.entity_version import EntityVersionFactory as BaseEntityVersionFactory
from base.tests.factories.user import UserFactory
from osis_common.document.xls_build import CONTENT_TYPE_XLS
from partnership.models import AgreementStatus, PartnershipType
from partnership.tests import TestCase
from partnership.tests.factories import FinancingFactory
from partnership.tests.factories import FundingTypeFactory
from partnership.tests.factories import (
    PartnerEntityFactory,
    PartnerFactory,
    PartnerTagFactory,
    PartnershipAgreementFactory,
    PartnershipEntityManagerFactory,
    PartnershipFactory,
    PartnershipTagFactory,
    PartnershipYearEducationLevelFactory,
    PartnershipYearFactory,
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

        class EducationGroupYearFactory(BaseEducationGroupYearFactory):
            management_entity = None
            administration_entity = None
            enrollment_campus = None
            main_teaching_campus = None

        cls.partnership_first_name = PartnershipFactory(
            partner__organization__name='Albania School',
        )

        # ucl_university
        parent = EntityVersionFactory(acronym='AAA', entity_type=SECTOR).entity
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
        cls.partnership_university_offer = PartnershipFactory()
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
        cls.partnership_partner = PartnershipFactory(partner=cls.partner)
        cls.partnership_partner_type = PartnershipFactory(
            partner__organization__type=ACADEMIC_PARTNER,
        )

        # partner_entity
        cls.partner_entity = PartnerEntityFactory()
        cls.partnership_partner_entity = PartnershipFactory(partner_entity=cls.partner_entity)

        # use_egracons
        cls.partnership_use_egracons = PartnershipFactory(partner__use_egracons=True)

        # city
        cls.partnership_city = PartnershipFactory(
            partner__contact_address__city='Berat',
            partner__contact_address__country__iso_code='AL',
        )

        # country
        cls.country = CountryFactory()
        partner_country = PartnerFactory(contact_address__country=cls.country)
        cls.partnership_country = PartnershipFactory(partner=partner_country)

        # continent
        cls.continent = Continent.objects.create(code='fo', name='foo')
        country_continent = CountryFactory(
            iso_code='FO',  # This is needed to prevent caching
            continent=cls.continent,
        )
        partner_continent = PartnerFactory(contact_address__country=country_continent)
        cls.partnership_continent = PartnershipFactory(partner=partner_continent)

        # partner_tags
        cls.partner_tag = PartnerTagFactory()
        partner_tag = PartnerFactory(tags=[cls.partner_tag])
        cls.partnership_partner_tags = PartnershipFactory(partner=partner_tag)

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
        cls.partnership_is_sms = PartnershipYearFactory(is_sms=True, academic_year__year=2150).partnership

        # is_smp
        cls.partnership_is_smp = PartnershipYearFactory(is_smp=True, academic_year__year=2151).partnership
        # is_sta
        cls.partnership_is_sta = PartnershipYearFactory(is_sta=True, academic_year__year=2152).partnership
        # is_stt
        cls.partnership_is_stt = PartnershipYearFactory(is_stt=True, academic_year__year=2153).partnership

        # partnership_type
        cls.partnership_type = PartnershipFactory(
            partnership_type=PartnershipType.GENERAL.name,
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_type,
            status=AgreementStatus.VALIDATED.name,
            end_date=date(2020, 7, 1),
        )
        PartnershipYearFactory(
            partnership=cls.partnership_type,
            academic_year__year=2154,
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
        cls.partnership_partnership_no_agreement_in = PartnershipFactory(years=[])
        PartnershipYearFactory(
            partnership=cls.partnership_partnership_no_agreement_in,
            academic_year__year=2180,
        )
        # All filters
        cls.country_all_filters = CountryFactory(
            iso_code='BA',  # This is needed to prevent caching
            continent=Continent.objects.create(code='ba', name='bar'),
        )
        sector = EntityVersionFactory(
            acronym='ZZZ',
            entity_type=SECTOR,
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
        cls.partnership_all_filters = PartnershipFactory(
            ucl_entity=labo.entity,
            partner=cls.partner_all_filters,
            comment='all_filters',
            partner_entity=PartnerEntityFactory(
                partner=cls.partner_all_filters,
            ),
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
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')

    def test_get_num_queries_serializer(self):
        self.client.force_login(self.user)
        with self.assertNumQueriesLessThan(11):
            self.client.get(self.url, HTTP_ACCEPT='application/json')

    def test_get_list_ordering(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?ordering=partner')
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        context = response.context_data
        self.assertEqual(context['partnerships'][0], self.partnership_first_name)

    def test_get_list_ordering_country(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?ordering=country')
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        context = response.context_data
        self.assertEqual(context['partnerships'][0], self.partnership_city)
        self.assertEqual(context['partnerships'][1], self.partnership_partner)

    def test_get_list_ordering_ucl(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?ordering=ucl')
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        context = response.context_data
        self.assertEqual(context['partnerships'][0], self.partnership_ucl_university_labo)
        self.assertEqual(context['partnerships'][1], self.partnership_ucl_university)

    def test_filter_ucl_university(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {
            'ucl_entity': self.ucl_university.pk,
            'ucl_entity_with_child': True,
            'ordering': 'ucl',
        })
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 2)
        self.assertEqual(context['partnerships'][0], self.partnership_ucl_university_labo)
        self.assertEqual(context['partnerships'][1], self.partnership_ucl_university)

        response = self.client.get(self.url, {
            'ucl_entity': self.ucl_university.pk,
            'ucl_entity_with_child': False,
        })
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_ucl_university)

    def test_filter_ucl_university_labo(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?ucl_entity=' + str(self.ucl_university_labo.pk))
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_ucl_university_labo)

    def test_filter_university_offers(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?university_offer=' + str(self.university_offer.pk))
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        context = response.context_data
        self.assertEqual(context['paginator'].count, 27)  # Include partnerships with offers at None

    def test_filter_partner(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?partner=' + str(self.partner.pk))
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_partner)

    def test_filter_partner_entity(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?partner_entity=' + str(self.partner_entity.pk))
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_partner_entity)
        
    def test_filter_use_egracons(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?use_egracons=True')
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_use_egracons)

    def test_filter_partner_type(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?partner_type=' + ACADEMIC_PARTNER)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_partner_type)

    def test_filter_city(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?city=Berat')
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_city)

    def test_filter_country(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?country=' + str(self.country.pk))
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_country)

    def test_filter_continent(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?continent=' + str(self.continent.pk))
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_continent)

    def test_filter_partner_tags(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?partner_tags=' + str(self.partner_tag.pk))
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_partner_tags)

    def test_filter_education_field(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?education_field=' + str(self.education_field.pk))
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_education_field)

    def test_filter_education_level(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?education_level=' + str(self.education_level.pk))
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_education_level)

    def test_filter_is_sms(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?is_sms=True')
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_is_sms)

    def test_filter_is_smp(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?is_smp=True')
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_is_smp)

    def test_filter_is_sta(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?is_sta=True')
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_is_sta)

    def test_filter_is_stt(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?is_stt=True')
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_is_stt)

    def test_filter_partnership_type(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {
            'partnership_type': PartnershipType.GENERAL.name,
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(self.partnership_type.uuid))
        self.assertEqual(results[0]['validity_end'], "01/07/2020")

    def test_filter_tags(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?tags=' + str(self.tag.pk))
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_tag)

    def test_filter_comment(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?comment=foo')
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_comment)

    def test_filter_partnership_in(self):
        self.client.force_login(self.user)
        academic_year = self.partnership_partnership_in.agreements.first().start_academic_year_id
        response = self.client.get(self.url + '?partnership_in=' + str(academic_year))
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_partnership_in)

    def test_filter_partnership_ending_in(self):
        self.client.force_login(self.user)
        academic_year = self.partnership_partnership_ending_in.agreements.first().end_academic_year_id
        response = self.client.get(self.url + '?partnership_ending_in=' + str(academic_year))
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_partnership_ending_in)

    def test_filter_partnership_valid_in(self):
        self.client.force_login(self.user)
        academic_year = self.partnership_partnership_valid_in.agreements.first().start_academic_year_id
        response = self.client.get(self.url + '?partnership_valid_in=' + str(academic_year))
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_partnership_valid_in)
        self.assertEqual(context['partnerships'][0].validity_end, "2118-19")

    def test_filter_partnership_not_valid_in(self):
        self.client.force_login(self.user)
        academic_year = self.partnership_partnership_not_valid_in.agreements.first().start_academic_year_id
        response = self.client.get(self.url + '?partnership_not_valid_in=' + str(academic_year))
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_partnership_not_valid_in)
        self.assertIsNone(context['partnerships'][0].validity_end)

    def test_filter_partnership_no_agreements_in(self):
        self.client.force_login(self.user)
        academic_year = self.partnership_partnership_no_agreement_in.years.first().academic_year_id
        response = self.client.get(self.url + '?partnership_with_no_agreements_in=' + str(academic_year))
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_partnership_no_agreement_in)

    def test_all_filters(self):
        self.client.force_login(self.user)
        query = '&'.join(['{0}={1}'.format(key, value) for key, value in {
            'ucl_entity': str(self.partnership_all_filters.ucl_entity_id),
            'university_offers': str(self.partnership_all_filters.years.filter(offers__isnull=False).first().offers.first().pk),
            'partner': str(self.partnership_all_filters.partner_id),
            'use_egracons': 'False',
            'partner_entity': str(self.partnership_all_filters.partner_entity_id),
            'city': 'all_filters',
            'country': str(self.country_all_filters.pk),
            'continent': str(self.country_all_filters.continent_id),
            'partner_tags': str(self.all_partner_tag.pk),
            'education_field': str(self.all_education_field.pk),
            'education_level': str(self.all_education_level.pk),
            'is_sms': 'False',
            'is_smp': 'False',
            'is_sta': 'False',
            'is_stt': 'False',
            'tags': str(self.all_partnership_tag.pk),
            'comment': 'all_filters',
            'partnership_in': str(AcademicYear.objects.get(year=2125).pk),
            'partnership_ending_in': str(AcademicYear.objects.get(year=2129).pk),
            'partnership_valid_in': str(AcademicYear.objects.get(year=2127).pk),
            'partnership_not_valid_in': str(AcademicYear.objects.get(year=2126).pk),
        }.items()])
        response = self.client.get(self.url + '?' + query)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_all_filters)

    def test_export_all(self):
        self.client.force_login(self.user)

        # We need more precise objects (on the correct academic year)
        year = AcademicYearFactory(year=2136)
        partnership1 = PartnershipFactory()
        partnership_year = PartnershipYearFactory(
            partnership=partnership1,
            academic_year=year,
        )
        partnership_year.education_levels.add(
            PartnershipYearEducationLevelFactory(),
            PartnershipYearEducationLevelFactory(),
        )
        partnership1.tags.add(PartnershipTagFactory(), PartnershipTagFactory())
        PartnershipAgreementFactory(
            partnership=partnership1,
            status=AgreementStatus.VALIDATED.name,
            start_academic_year=year,
            end_academic_year__year=2137,
        )
        financing = FinancingFactory(academic_year=year)
        financing.countries.add(partnership1.partner.contact_address.country)

        partnership2 = PartnershipFactory(
            partnership_type=PartnershipType.PROJECT.name,
        )
        PartnershipYearFactory(
            partnership=partnership2,
            academic_year=year,
            subtype=PartnershipSubtypeFactory(),
            funding_type=FundingTypeFactory(),
        )
        PartnershipAgreementFactory(
            partnership=partnership2,
            status=AgreementStatus.VALIDATED.name,
            start_academic_year=year,
            end_academic_year__year=2137,
        )

        url = resolve_url('partnerships:export', academic_year_pk=year.pk)
        with self.assertNumQueriesLessThan(24):
            response = self.client.get(url)
            self.assertEqual(response['Content-Type'], CONTENT_TYPE_XLS)
        self.assertTemplateNotUsed(response, 'partnerships/partnership/partnership_list.html')
