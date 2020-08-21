from datetime import date, timedelta

from django.shortcuts import resolve_url
from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from base.models.enums.entity_type import FACULTY, SECTOR
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory
from partnership.models import PartnershipType
from partnership.tests.factories import (
    FundingTypeFactory,
    PartnerEntityFactory,
    PartnerFactory,
    PartnershipEntityManagerFactory,
    PartnershipFactory,
    PartnershipMissionFactory,
    PartnershipSubtypeFactory,
    PartnershipYearEducationLevelFactory,
    PartnershipYearFactory,
    UCLManagementEntityFactory,
)
from reference.tests.factories.domain_isced import DomainIscedFactory


class PartnershipCreateGeneralViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(
            entity=entity_version.entity,
            person__user=cls.user,
            scopes=[PartnershipType.GENERAL.name]
        )

        cls.partner = PartnerFactory()
        cls.partner_entity = PartnerEntityFactory(partner=cls.partner)

        AcademicYearFactory.produce_in_future(date.today().year, 3)

        cls.education_field = DomainIscedFactory()
        cls.education_level = PartnershipYearEducationLevelFactory()

        cls.url = resolve_url('partnerships:create',
                              type=PartnershipType.GENERAL)

        # Ucl
        root = EntityVersionFactory(parent=None).entity
        sector = EntityVersionFactory(entity_type=SECTOR, parent=root).entity
        cls.ucl_university = EntityVersionFactory(
            parent=sector,
            entity_type=FACULTY,
        ).entity
        cls.ucl_university_labo = EntityVersionFactory(
            parent=cls.ucl_university,
        ).entity
        UCLManagementEntityFactory(entity=cls.ucl_university)

        cls.university_offer = EducationGroupYearFactory(
            administration_entity=cls.ucl_university_labo,
        )

        cls.data = {
            'partnership_type': PartnershipType.GENERAL.name,
            'comment': '',
            'partner': cls.partner.pk,
            'partner_entity': cls.partner_entity.pk,
            'supervisor': PersonFactory().pk,
            'ucl_entity': cls.ucl_university.pk,
            'university_offers': [cls.university_offer.pk],
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=365),
            'year-is_sms': True,
            'year-is_smp': False,
            'year-is_sta': True,
            'year-is_stt': False,
            'year-education_fields': [cls.education_field.pk],
            'year-education_levels': [cls.education_level.pk],
            'year-entities': [],
            'year-offers': [],
            'year-funding_type': FundingTypeFactory().pk,
            'year-missions': PartnershipMissionFactory().pk,
            'year-subtype': PartnershipSubtypeFactory().pk,
        }

    def test_get_view_as_adri(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(
            response,
            'partnerships/partnership/partnership_create.html',
        )

    def test_post(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertTemplateUsed(
            response,
            'partnerships/partnership/partnership_detail.html',
        )

    def test_post_bad_dates(self):
        self.client.force_login(self.user)
        data = self.data.copy()
        data['start_date'] = data['end_date']
        data['end_date'] = date.today()
        response = self.client.post(self.url, data=data, follow=True)
        self.assertIn(
            _("End date must be after start date"),
            response.context['form'].errors['__all__'],
        )


class PartnershipUpdateGeneralViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(
            entity=entity_version.entity,
            person__user=cls.user,
            scopes=[PartnershipType.GENERAL.name]
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
        root = EntityVersionFactory(parent=None).entity
        sector = EntityVersionFactory(entity_type=SECTOR, parent=root).entity
        cls.ucl_university = EntityVersionFactory(
            parent=sector,
            entity_type=FACULTY,
        ).entity
        UCLManagementEntityFactory(entity=cls.ucl_university)
        cls.ucl_university_labo = EntityVersionFactory(
            parent=cls.ucl_university,
        ).entity
        UCLManagementEntityFactory(entity=cls.ucl_university_labo)

        cls.partnership = PartnershipFactory(
            partnership_type=PartnershipType.GENERAL.name,
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

        cls.subtype1 = PartnershipSubtypeFactory()
        cls.subtype2 = PartnershipSubtypeFactory()
        cls.data = {
            'comment': '',
            'partner': cls.partner.pk,
            'partner_entity': cls.partner_entity.pk,
            'supervisor': cls.user.person.pk,
            'ucl_entity': cls.ucl_university_labo.pk,
            'start_date': cls.start_academic_year.start_date,
            'end_date': cls.end_academic_year.end_date,
            'year-is_sms': True,
            'year-is_smp': False,
            'year-is_sta': True,
            'year-is_stt': False,
            'year-education_fields': [cls.education_field.pk],
            'year-education_levels': [cls.education_level.pk],
            'year-entities': [],
            'year-offers': [],
            'year-funding_type': FundingTypeFactory().pk,
            'year-missions': [
                PartnershipMissionFactory().pk,
                PartnershipMissionFactory().pk,
            ],
            'year-subtype': cls.subtype1.pk,
        }

    def test_get_own_partnership_as_adri(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_update.html')

    def test_post_partnership(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')

    def test_remove_partnership_year(self):
        self.client.force_login(self.user)
        self.assertEqual(self.partnership.years.count(), 3)
        data = self.data.copy()
        data['start_date'] = date(2152, 1, 1)
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')
        self.partnership.refresh_from_db()
        self.assertEqual(self.partnership.years.count(), 2)

    def test_subtype_deactivation(self):
        self.client.force_login(self.user)
        # Save subtype 1
        self.client.post(self.url, data=self.data, follow=True)

        response = self.client.get(self.url)
        field = response.context_data['form_year'].fields['subtype']
        self.assertIn(self.subtype1, field.queryset)
        self.assertIn(self.subtype2, field.queryset)

        # If we deactivate both subtypes, we should still have the 1 set
        self.subtype1.is_active = False
        self.subtype1.save()
        self.subtype2.is_active = False
        self.subtype2.save()

        response = self.client.get(self.url)
        field = response.context_data['form_year'].fields['subtype']
        self.assertIn(self.subtype1, field.queryset)
        self.assertNotIn(self.subtype2, field.queryset)
