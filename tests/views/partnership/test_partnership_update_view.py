from datetime import timedelta

from django.contrib.auth.models import Permission
from django.core import mail
from django.forms import ModelChoiceField
from django.shortcuts import resolve_url
from django.test import TestCase
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from base.models.enums.entity_type import FACULTY, SECTOR
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory
from partnership.models import (
    Partnership,
    PartnershipConfiguration,
    PartnershipType,
)
from partnership.tests.factories import (
    PartnerEntityFactory,
    PartnerFactory,
    PartnershipEntityManagerFactory,
    PartnershipFactory,
    PartnershipMissionFactory, PartnershipTagFactory,
    PartnershipYearEducationLevelFactory,
    PartnershipYearFactory,
    UCLManagementEntityFactory,
)
from reference.tests.factories.domain_isced import DomainIscedFactory


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
        cls.user_project = UserFactory()
        PartnershipEntityManagerFactory(
            entity=entity_version.entity,
            person__user=cls.user_project,
            scopes=[PartnershipType.PROJECT.name]
        )

        access_perm = Permission.objects.get(name='can_access_partnerships')
        cls.user.user_permissions.add(access_perm)
        cls.user_adri.user_permissions.add(access_perm)
        cls.user_gs.user_permissions.add(access_perm)
        cls.user_gf.user_permissions.add(access_perm)
        cls.user_other_gf.user_permissions.add(access_perm)
        cls.user_project.user_permissions.add(access_perm)

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

        # Initialize config
        PartnershipConfiguration.objects.update(
            partnership_creation_update_min_year_id=cls.academic_year_2149.pk
        )

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
            ucl_entity=cls.ucl_university,
        )
        cls.url = resolve_url('partnerships:update', pk=cls.partnership.pk)

        cls.other_partnership = PartnershipFactory(
            partnership_type=PartnershipType.PROJECT.name,
        )
        cls.other_url = resolve_url('partnerships:update', pk=cls.other_partnership.pk)

        cls.data = {
            'partnership_type': PartnershipType.MOBILITY.name,
            'comment': '',
            'partner': cls.partner.pk,
            'partner_entity': cls.partner_entity.pk,
            'supervisor': '',
            'ucl_entity': cls.ucl_university_labo.pk,
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
            'year-missions': [PartnershipMissionFactory().pk],
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

    def test_get_other_partnership_type_as_anonymous(self):
        response = self.client.get(self.other_url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnership/partnership_update.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_other_partnership_type_as_authenticated(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.other_url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnership/partnership_update.html')

    def test_get_other_partnership_type_as_correct_user(self):
        self.client.force_login(self.user_project)
        response = self.client.get(self.other_url)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_update.html')

    def test_get_end_date_too_early(self):
        self.client.force_login(self.user_adri)

        prev_value = PartnershipConfiguration.get_configuration().partnership_creation_update_min_year_id

        # Put config year too far
        PartnershipConfiguration.objects.update(
            partnership_creation_update_min_year_id=self.academic_year_2153.pk,
        )

        response = self.client.get(self.url)
        self.assertEqual(
            response.context['form_year'].fields['end_academic_year'].initial,
            self.academic_year_2153,
        )
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_update.html')

        # Put back config
        PartnershipConfiguration.objects.update(
            partnership_creation_update_min_year_id=prev_value,
        )

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
            str(partnership.partner_id),
            str(data['partner']),
        )
        self.assertEqual(
            str(partnership.partner_entity_id),
            str(data['partner_entity']),
        )
        self.assertEqual(
            str(partnership.supervisor_id if partnership.supervisor is not None else None),
            str(data['supervisor'] if data['supervisor'] is not '' else None),
        )
        self.assertEqual(
            str(partnership.ucl_entity_id),
            str(data['ucl_entity']),
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

    def test_post_notify_new_end_date(self):
        self.client.force_login(self.user_gf)
        data = self.data.copy()
        data['year-end_academic_year'] = str(self.academic_year_2153.pk)
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(str(self.user_gf), mail.outbox[0].body)
        mail.outbox = []

    def test_post_invalid_ucl_university(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        data['ucl_entity'] = self.ucl_university_not_choice.pk
        response = self.client.post(self.url, data=data)
        invalid_choice = ModelChoiceField.default_error_messages['invalid_choice']
        self.assertFormError(response, 'form', 'ucl_entity', invalid_choice)

    def test_post_invalid_levels(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        data['year-education_levels'] = []
        response = self.client.post(self.url, data=data)
        msg = _('education_levels_empty_errors')
        self.assertFormError(response, 'form_year', 'education_levels', msg)

    def test_post_invalid_years(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        data['year-end_academic_year'] = self.start_academic_year.pk
        data['year-start_academic_year'] = self.end_academic_year.pk
        response = self.client.post(self.url, data=data)
        msg = _('start_date_after_end_date')
        self.assertFormError(response, 'form_year', 'start_academic_year', msg)
        msg = _('start_date_after_from_date')
        self.assertFormError(response, 'form_year', 'start_academic_year', msg)
        msg = _('from_date_after_end_date')
        self.assertFormError(response, 'form_year', 'from_academic_year', msg)

    def test_post_invalid_partner(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        partner = PartnerFactory(end_date=timezone.now() - timedelta(days=1))
        data['partner'] = partner.pk
        response = self.client.post(self.url, data=data)
        msg = _('partnership_inactif_partner_error')
        self.assertFormError(response, 'form', 'partner', msg)

        data = self.data.copy()
        data['partner_entity'] = PartnerEntityFactory().pk
        response = self.client.post(self.url, data=data)
        msg = _('invalid_partner_entity')
        self.assertFormError(response, 'form', 'partner_entity', msg)

    def test_post_invalid_ucl_university_labo(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        data['ucl_entity'] = self.ucl_university_not_choice.pk
        response = self.client.post(self.url, data=data)
        invalid_choice = ModelChoiceField.default_error_messages['invalid_choice']
        self.assertFormError(response, 'form', 'ucl_entity', invalid_choice)

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
