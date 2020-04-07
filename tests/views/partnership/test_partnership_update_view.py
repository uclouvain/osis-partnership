from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from base.models.enums.entity_type import FACULTY
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory
from partnership.models import Partnership
from partnership.tests.factories import (
    PartnerEntityFactory, PartnerFactory,
    PartnershipEntityManagerFactory,
    PartnershipFactory,
    PartnershipYearEducationFieldFactory,
    PartnershipYearEducationLevelFactory,
    PartnershipYearFactory,
    UCLManagementEntityFactory,
    PartnershipTagFactory,
)


class PartnershipUpdateViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.user_gs = UserFactory()
        cls.user_gf = UserFactory()
        cls.user_other_gf = UserFactory()

        cls.user.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))
        cls.user_adri.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))
        cls.user_gs.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))
        cls.user_gf.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))
        cls.user_other_gf.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))

        # Dates :
        cls.partner = PartnerFactory()
        cls.partner_entity = PartnerEntityFactory(partner=cls.partner)

        # Years
        cls.academic_year_2000 = AcademicYearFactory(year=2000)
        cls.academic_year_2149 = AcademicYearFactory(year=2149)
        cls.start_academic_year = AcademicYearFactory(year=2150)
        cls.from_academic_year = AcademicYearFactory(year=2151)
        cls.end_academic_year = AcademicYearFactory(year=2152)
        cls.academic_year_2153 = AcademicYearFactory(year=2153)

        cls.education_field = PartnershipYearEducationFieldFactory()
        cls.education_level = PartnershipYearEducationLevelFactory()

        # Ucl
        sector = EntityFactory()
        cls.ucl_university = EntityFactory()
        EntityVersionFactory(entity=cls.ucl_university, parent=sector, entity_type=FACULTY)
        cls.ucl_university_labo = EntityFactory()
        EntityVersionFactory(entity=cls.ucl_university_labo, parent=cls.ucl_university)
        UCLManagementEntityFactory(entity=cls.ucl_university_labo)
        cls.ucl_university_not_choice = EntityFactory()
        EntityVersionFactory(entity=cls.ucl_university, entity_type=FACULTY)
        cls.ucl_university_labo_not_choice = EntityFactory()
        EntityVersionFactory(entity=cls.ucl_university_labo, parent=cls.ucl_university)
        cls.university_offer = EducationGroupYearFactory(administration_entity=cls.ucl_university_labo)

        PartnershipEntityManagerFactory(person__user=cls.user_gs, entity=sector)
        entity_manager = PartnershipEntityManagerFactory(person__user=cls.user_gf, entity=cls.ucl_university)
        PartnershipEntityManagerFactory(person__user=cls.user_other_gf, entity=cls.ucl_university)

        cls.partner_gf = PartnerFactory(author=cls.user_gf.person)
        cls.partnership = PartnershipFactory(
            partner=cls.partner,
            partner_entity=cls.partner_entity,
            author=cls.user_gf.person,
            years=[
                PartnershipYearFactory(academic_year=cls.start_academic_year),
                PartnershipYearFactory(academic_year=cls.from_academic_year),
                PartnershipYearFactory(academic_year=cls.end_academic_year),
            ],
            ucl_university=cls.ucl_university,
        )
        cls.url = reverse('partnerships:update', kwargs={'pk': cls.partnership.pk})

        cls.data = {
            'comment': '',
            'partner': cls.partner.pk,
            'partner_entity': cls.partner_entity.pk,
            'supervisor': '',
            'ucl_university': cls.ucl_university.pk,
            'ucl_university_labo': cls.ucl_university_labo.pk,
            'year-is_sms': True,
            'year-is_smp': False,
            'year-is_sta': True,
            'year-is_stt': False,
            'year-education_fields': [cls.education_field.pk],
            'year-education_levels': [cls.education_level.pk],
            'year-entities': [],
            'year-offers': [],
            'year-start_academic_year': cls.start_academic_year.pk,
            'year-from_academic_year': cls.from_academic_year.pk,
            'year-end_academic_year': cls.end_academic_year.pk,
        }

    def test_get_partnership_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnership/partnership_update.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_partnership_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnership/partnership_update.html')

    def test_get_own_partnership_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_update.html')

    def test_get_own_partnership_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_update.html')
        self.assertNotIn('start_academic_year', response.context_data['form_year'].fields)

    def test_get_own_partnership_as_gs(self):
        self.client.force_login(self.user_gs)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_update.html')
        self.assertNotIn('start_academic_year', response.context_data['form_year'].fields)

    def test_get_other_partnership_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_update.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        data = self.data
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')
        partnership = Partnership.objects.get(pk=self.partnership.pk)
        self.assertEqual(
            partnership.comment,
            data['comment'],
        )
        self.assertEqual(
            str(partnership.partner.pk),
            str(data['partner']),
        )
        self.assertEqual(
            str(partnership.partner_entity.pk),
            str(data['partner_entity']),
        )
        self.assertEqual(
            str(partnership.supervisor.pk if partnership.supervisor is not None else None),
            str(data['supervisor'] if data['supervisor'] is not '' else None),
        )
        self.assertEqual(
            str(partnership.ucl_university.pk),
            str(data['ucl_university']),
        )
        self.assertEqual(
            str(partnership.ucl_university_labo.pk),
            str(data['ucl_university_labo']),
        )
        self.assertEqual(
            [pk for pk in partnership.end_partnership_year.education_fields.values_list('pk', flat=True)],
            data['year-education_fields'],
        )
        self.assertEqual(
            [pk for pk in partnership.end_partnership_year.education_levels.values_list('pk', flat=True)],
            data['year-education_levels'],
        )
        self.assertEqual(
            list(partnership.end_partnership_year.entities.values_list('pk', flat=True)),
            data['year-entities'],
        )
        self.assertEqual(
            list(partnership.end_partnership_year.offers.values_list('pk', flat=True)),
            data['year-offers'],
        )
        self.assertEqual(
            str(partnership.start_academic_year.pk),
            str(data['year-start_academic_year']),
        )
        self.assertEqual(
            str(partnership.end_academic_year.pk),
            str(data['year-end_academic_year']),
        )

    def test_post_empty(self):
        self.client.force_login(self.user_adri)
        response = self.client.post(self.url, data={}, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnership/partnership_detail.html')
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_update.html')

    def test_post_empty_sm(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        data['year-is_sms'] = False
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')
        year = response.context_data['partnership'].years.last()
        self.assertFalse(year.education_levels.exists())
        self.assertFalse(year.entities.exists())
        self.assertFalse(year.offers.exists())

    def test_post_past_start_date(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        data['year-start_academic_year'] = str(self.academic_year_2149.pk)
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')
        self.assertEqual(response.context_data['partnership'].years.count(), 4)

    def test_post_post_start_date(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        data['year-start_academic_year'] = str(self.from_academic_year.pk)
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')
        self.assertEqual(response.context_data['partnership'].years.count(), 2)

    def test_post_past_from_date(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        data['year-from_academic_year'] = str(self.start_academic_year.pk)
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')
        self.assertEqual(response.context_data['partnership'].years.count(), 3)
        self.assertTrue(response.context_data['partnership'].years.first().is_sms)

    def test_post_post_from_date(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        data['year-from_academic_year'] = str(self.end_academic_year.pk)
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')
        self.assertEqual(response.context_data['partnership'].years.count(), 3)
        self.assertFalse(response.context_data['partnership'].years.first().is_sms)
        self.assertFalse(response.context_data['partnership'].years.all()[1].is_sms)
        self.assertTrue(response.context_data['partnership'].years.last().is_sms)

    def test_post_past_end_date(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        data['year-end_academic_year'] = str(self.academic_year_2153.pk)
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')
        self.assertEqual(response.context_data['partnership'].years.count(), 4)

    def test_post_invalid_ucl_university(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        data['ucl_university'] = self.ucl_university_not_choice.pk
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnership/partnership_detail.html')
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_update.html')

    def test_post_invalid_ucl_university_labo(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        data['ucl_university_labo'] = self.ucl_university_not_choice.pk
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnership/partnership_detail.html')
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_update.html')

    def test_post_post_end_date(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        data['year-end_academic_year'] = str(self.from_academic_year.pk)
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')
        self.assertEqual(response.context_data['partnership'].years.count(), 2)

    def test_post_partnership_as_gs(self):
        self.client.force_login(self.user_gs)
        data = {**self.data, **{
            'tags': [PartnershipTagFactory(value="Foobar").pk],
            'comment': 'Lorem ipsum',
        }}
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')
        self.assertContains(response, "Foobar")
        self.assertContains(response, "Lorem ipsum")
