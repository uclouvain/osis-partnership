from datetime import date, timedelta

from django.contrib.auth.models import Permission
from django.core import mail
from django.forms import ModelChoiceField
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
    FundingTypeFactory, PartnerEntityFactory, PartnerFactory,
    PartnershipEntityManagerFactory,
    PartnershipYearEducationLevelFactory,
    UCLManagementEntityFactory,
)
from reference.tests.factories.domain_isced import DomainIscedFactory


class PartnershipCreateViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.user_gs = UserFactory()
        cls.user_gf = UserFactory()
        cls.user_other_gf = UserFactory()
        cls.user_2_types = UserFactory()
        PartnershipEntityManagerFactory(
            entity=entity_version.entity,
            person__user=cls.user_2_types,
            scopes=[PartnershipType.MOBILITY.name, PartnershipType.GENERAL.name]
        )

        access_perm = Permission.objects.get(name='can_access_partnerships')
        cls.user.user_permissions.add(access_perm)
        cls.user_adri.user_permissions.add(access_perm)
        cls.user_gs.user_permissions.add(access_perm)
        cls.user_gf.user_permissions.add(access_perm)
        cls.user_other_gf.user_permissions.add(access_perm)
        cls.user_2_types.user_permissions.add(access_perm)

        cls.partner = PartnerFactory()
        cls.partner_entity = PartnerEntityFactory(partner=cls.partner)

        cls.start_academic_year = AcademicYearFactory(year=2150)
        cls.end_academic_year = AcademicYearFactory(year=2151)
        year = date.today().year
        AcademicYearFactory(year=year)
        AcademicYearFactory(year=year + 1)
        AcademicYearFactory(year=year + 2)

        cls.education_field = DomainIscedFactory()
        cls.education_level = PartnershipYearEducationLevelFactory()

        cls.url = reverse('partnerships:create')
        cls.mobility_url = reverse(
            'partnerships:create',
            kwargs={'type': PartnershipType.MOBILITY},
        )

        # Ucl
        sector = EntityFactory()
        EntityVersionFactory(entity=sector, entity_type=SECTOR)
        cls.ucl_university = EntityFactory()
        EntityVersionFactory(entity=cls.ucl_university, parent=sector, entity_type=FACULTY)
        cls.ucl_university_labo = EntityFactory()
        EntityVersionFactory(entity=cls.ucl_university_labo, parent=cls.ucl_university)
        UCLManagementEntityFactory(entity=cls.ucl_university)
        UCLManagementEntityFactory()

        cls.ucl_university_not_choice = EntityFactory()
        EntityVersionFactory(entity=cls.ucl_university_not_choice, entity_type=FACULTY)
        cls.ucl_university_labo_not_choice = EntityFactory()
        EntityVersionFactory(
            entity=cls.ucl_university_labo_not_choice,
            parent=cls.ucl_university_not_choice,
        )
        cls.university_offer = EducationGroupYearFactory(administration_entity=cls.ucl_university_labo)

        PartnershipEntityManagerFactory(person__user=cls.user_gs, entity=sector)
        PartnershipEntityManagerFactory(person__user=cls.user_gf, entity=cls.ucl_university)
        PartnershipEntityManagerFactory(person__user=cls.user_other_gf, entity=cls.ucl_university)
        PartnershipEntityManagerFactory(person__user=cls.user_2_types, entity=cls.ucl_university)

        cls.data = {
            'partnership_type': PartnershipType.MOBILITY.name,
            'comment': '',
            'partner': cls.partner.pk,
            'partner_entity': cls.partner_entity.pk,
            'supervisor': '',
            'ucl_entity': cls.ucl_university.pk,
            'university_offers': [cls.university_offer.pk],
            'year-is_sms': True,
            'year-is_smp': False,
            'year-is_sta': True,
            'year-is_stt': False,
            'year-education_fields': [cls.education_field.pk],
            'year-education_levels': [cls.education_level.pk],
            'year-entities': [],
            'year-offers': [],
            'year-start_academic_year': cls.start_academic_year.pk,
            'year-end_academic_year': cls.end_academic_year.pk,
        }

    def test_get_view_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnership/type_choose.html.html')
        self.assertTemplateUsed(response, 'access_denied.html')
        response = self.client.get(self.mobility_url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnership/partnership_create.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnership/type_choose.html')
        self.assertTemplateUsed(response, 'access_denied.html')
        response = self.client.get(self.mobility_url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnership/partnership_create.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnership/type_choose.html')
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_create.html')

    def test_get_view_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnership/type_choose.html')
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_create.html')

    def test_get_view_as_gs(self):
        self.client.force_login(self.user_gs)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnership/type_choose.html')
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_create.html')

    def test_get_choose_view(self):
        self.client.force_login(self.user_2_types)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partnership/type_choose.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        data = self.data
        response = self.client.post(self.mobility_url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')
        self.assertEqual(len(mail.outbox), 0)

    def test_post_past_start_date_as_adri(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        data['year-start_academic_year'] = str(AcademicYearFactory(year=2000).pk)
        response = self.client.post(self.mobility_url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')

    def test_post_past_start_date_as_gf(self):
        self.client.force_login(self.user_gf)
        data = self.data.copy()
        data['year-start_academic_year'] = str(AcademicYearFactory(year=2000).pk)
        response = self.client.post(self.mobility_url, data=data, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnership/partnership_detail.html')
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_create.html')

    def test_post_post_start_date_as_adri(self):
        self.client.force_login(self.user_adri)
        data = self.data
        response = self.client.post(self.mobility_url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')

    def test_post_ucl_university_invalid_as_adri(self):
        self.client.force_login(self.user_adri)
        data = self.data
        data['ucl_entity'] = self.ucl_university_not_choice.pk
        response = self.client.post(self.mobility_url, data=data)
        invalid_choice = ModelChoiceField.default_error_messages['invalid_choice']
        self.assertFormError(response, 'form', 'ucl_entity', invalid_choice)

    def test_post_ucl_university_labo_invalid_as_adri(self):
        self.client.force_login(self.user_adri)
        data = self.data
        data['ucl_entity'] = self.ucl_university_labo_not_choice.pk
        response = self.client.post(self.mobility_url, data=data)
        invalid_choice = ModelChoiceField.default_error_messages['invalid_choice']
        self.assertFormError(response, 'form', 'ucl_entity', invalid_choice)

    def test_post_post_start_date_as_gf(self):
        self.client.force_login(self.user_gf)
        data = self.data
        response = self.client.post(self.mobility_url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(str(self.user_gf), mail.outbox[0].body)
        mail.outbox = []

    def test_post_post_start_date_as_gs(self):
        self.client.force_login(self.user_gs)
        data = self.data
        response = self.client.post(self.mobility_url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(str(self.user_gs), mail.outbox[0].body)
        mail.outbox = []


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
        access_perm = Permission.objects.get(name='can_access_partnerships')
        cls.user.user_permissions.add(access_perm)

        cls.partner = PartnerFactory()
        cls.partner_entity = PartnerEntityFactory(partner=cls.partner)

        AcademicYearFactory.produce_in_future(date.today().year, 3)

        cls.education_field = DomainIscedFactory()
        cls.education_level = PartnershipYearEducationLevelFactory()

        cls.url = reverse(
            'partnerships:create',
            kwargs={'type': PartnershipType.GENERAL},
        )

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
        }

    def test_get_view_as_adri(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_create.html')

    def test_post(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')
