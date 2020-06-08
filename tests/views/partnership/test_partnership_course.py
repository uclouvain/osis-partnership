from datetime import date

from django.shortcuts import resolve_url
from django.test import TestCase
from django.urls import reverse

from base.models.enums.entity_type import FACULTY, SECTOR
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory
from partnership.models import PartnershipType
from partnership.tests.factories import (
    FundingTypeFactory, PartnerEntityFactory,
    PartnerFactory,
    PartnershipEntityManagerFactory,
    PartnershipFactory, PartnershipYearEducationLevelFactory,
    PartnershipYearFactory, UCLManagementEntityFactory,
)
from partnership.tests.factories.partnership_year import \
    (
    PartnershipMissionFactory,
    PartnershipSubtypeFactory,
)
from reference.tests.factories.domain_isced import DomainIscedFactory


class PartnershipCreateCourseViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(
            entity=entity_version.entity,
            person__user=cls.user,
            scopes=[PartnershipType.COURSE.name]
        )

        cls.partner = PartnerFactory()
        cls.partner_entity = PartnerEntityFactory(partner=cls.partner)

        AcademicYearFactory.produce_in_future(date.today().year, 3)

        cls.education_field = DomainIscedFactory()
        cls.education_level = PartnershipYearEducationLevelFactory()

        cls.url = reverse(
            'partnerships:create',
            kwargs={'type': PartnershipType.COURSE},
        )

        cls.start_academic_year = AcademicYearFactory(year=2150)
        cls.end_academic_year = AcademicYearFactory(year=2151)
        year = date.today().year
        AcademicYearFactory(year=year)
        AcademicYearFactory(year=year + 1)
        AcademicYearFactory(year=year + 2)

        # Ucl
        sector = EntityFactory()
        EntityVersionFactory(entity=sector, entity_type=SECTOR)
        cls.ucl_university = EntityFactory()
        EntityVersionFactory(entity=cls.ucl_university, parent=sector, entity_type=FACULTY)
        cls.ucl_university_labo = EntityFactory()
        EntityVersionFactory(entity=cls.ucl_university_labo, parent=cls.ucl_university)
        UCLManagementEntityFactory(entity=cls.ucl_university)

        cls.university_offer = EducationGroupYearFactory(administration_entity=cls.ucl_university_labo)

        cls.data = {
            'partnership_type': PartnershipType.COURSE.name,
            'comment': '',
            'partner': cls.partner.pk,
            'partner_entity': cls.partner_entity.pk,
            'supervisor': PersonFactory().pk,
            'ucl_entity': cls.ucl_university.pk,
            'university_offers': [cls.university_offer.pk],
            'year-education_fields': [cls.education_field.pk],
            'year-education_levels': [cls.education_level.pk],
            'year-entities': [],
            'year-offers': [],
            'year-start_academic_year': cls.start_academic_year.pk,
            'year-end_academic_year': cls.end_academic_year.pk,
            'year-funding_type': FundingTypeFactory().pk,
            'year-missions': PartnershipMissionFactory().pk,
            'year-subtype': PartnershipSubtypeFactory().pk,
        }

    def test_get_view_as_adri(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_create.html')

    def test_post(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')


class PartnershipUpdateCourseViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(
            entity=entity_version.entity,
            person__user=cls.user,
            scopes=[PartnershipType.COURSE.name]
        )

        # Dates :
        cls.partner = PartnerFactory()
        cls.partner_entity = PartnerEntityFactory(partner=cls.partner)

        # Years
        cls.start_academic_year = AcademicYearFactory(year=2150)
        cls.from_academic_year = AcademicYearFactory(year=2151)
        cls.end_academic_year = AcademicYearFactory(year=2152)

        cls.education_field = DomainIscedFactory()
        cls.education_level = PartnershipYearEducationLevelFactory()

        # Ucl
        sector = EntityFactory()
        EntityVersionFactory(entity=sector, entity_type=SECTOR)
        cls.ucl_university = EntityFactory()
        EntityVersionFactory(entity=cls.ucl_university, parent=sector, entity_type=FACULTY)
        UCLManagementEntityFactory(entity=cls.ucl_university)
        cls.ucl_university_labo = EntityFactory()
        EntityVersionFactory(entity=cls.ucl_university_labo, parent=cls.ucl_university)
        UCLManagementEntityFactory(entity=cls.ucl_university_labo)

        cls.partnership = PartnershipFactory(
            partnership_type=PartnershipType.COURSE.name,
            partner=cls.partner,
            partner_entity=cls.partner_entity,
            author=cls.user.person,
            years=[
                PartnershipYearFactory(academic_year=cls.start_academic_year),
                PartnershipYearFactory(academic_year=cls.from_academic_year),
                PartnershipYearFactory(academic_year=cls.end_academic_year),
            ],
            ucl_entity=cls.ucl_university,
        )
        cls.url = resolve_url('partnerships:update', pk=cls.partnership.pk)

        cls.data = {
            'comment': '',
            'partner': cls.partner.pk,
            'partner_entity': cls.partner_entity.pk,
            'supervisor': cls.user.person.pk,
            'ucl_entity': cls.ucl_university_labo.pk,
            'year-start_academic_year': cls.start_academic_year.pk,
            'year-end_academic_year': cls.end_academic_year.pk,
            'year-from_academic_year': cls.from_academic_year.pk,
            'year-education_fields': [cls.education_field.pk],
            'year-education_levels': [cls.education_level.pk],
            'year-entities': [],
            'year-offers': [],
            'year-funding_type': FundingTypeFactory().pk,
            'year-missions': [
                PartnershipMissionFactory().pk,
                PartnershipMissionFactory().pk,
            ],
            'year-subtype': PartnershipSubtypeFactory().pk,
        }

    def test_get_own_partnership_as_adri(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_update.html')

    def test_post_partnership(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')