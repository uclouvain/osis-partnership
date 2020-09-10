from datetime import date, timedelta

from django.core import mail
from django.urls import reverse

from base.models.enums.entity_type import SECTOR, FACULTY
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory
from partnership.models import (
    AgreementStatus,
    MediaVisibility,
    PartnershipType,
)
from partnership.tests import TestCase
from partnership.tests.factories import (
    PartnershipAgreementFactory,
    PartnershipEntityManagerFactory,
    PartnershipFactory,
)


class PartnershipAgreementsListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # ucl_university
        root = EntityVersionFactory(parent=None).entity
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
        cls.ucl_university_labo = EntityVersionFactory(
            parent=cls.ucl_university,
            acronym='AAA',
        ).entity

        cls.user = PartnershipEntityManagerFactory().person.user
        cls.user_adri = UserFactory()

        root = EntityVersionFactory(parent=None).entity
        PartnershipEntityManagerFactory(
            entity=EntityVersionFactory(acronym='ADRI', parent=root).entity,
            person__user=cls.user_adri,
        )

        PartnershipAgreementFactory(
            partnership__ucl_entity=cls.ucl_university_labo,
        )
        PartnershipAgreementFactory(
            partnership__ucl_entity=cls.ucl_university_labo,
        )
        PartnershipAgreementFactory(
            partnership__ucl_entity=cls.ucl_university_labo,
            partnership__partnership_type=PartnershipType.COURSE.name,
            partnership__start_date=date(2017, 9, 1),
            partnership__end_date=date(2030, 9, 1),
            start_date=date(2017, 9, 1),
            end_date=date(2025, 9, 1),
        )

        cls.url = reverse('partnerships:agreements-list')
        cls.export_url = reverse('partnerships:export_agreements')

    def test_get_list_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/agreements/agreement_list.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_list_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/agreements/agreement_list.html')

    def test_num_queries_serializer(self):
        self.client.force_login(self.user)
        with self.assertNumQueriesLessThan(10):
            self.client.get(self.url, HTTP_ACCEPT='application/json')

    def test_get_list_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/agreements/agreement_list.html')

    def test_filter_special_dates_stopping(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url, {
            'partnership_special_dates_type': 'stopping',
            'partnership_special_dates_0': '25/06/2024',
            'partnership_special_dates_1': '05/07/2026',
        }, HTTP_ACCEPT='application/json')
        results = response.json()['object_list']
        self.assertEqual(len(results), 1)

    def test_export_anonymous(self):
        response = self.client.get(self.export_url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/agreements/agreement_list.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_export_as_authenticated(self):
        self.client.force_login(self.user)
        with self.assertNumQueriesLessThan(18):
            response = self.client.get(self.export_url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_export_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.export_url, follow=True)
        self.assertEqual(response.status_code, 200)


class PartnershipAgreementCreateViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # User creation
        cls.user = PartnershipEntityManagerFactory().person.user
        cls.user_adri = UserFactory()
        root = EntityVersionFactory(parent=None).entity
        entity_version = EntityVersionFactory(acronym='ADRI', parent=root)
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.user_gf = UserFactory()
        entity_manager = PartnershipEntityManagerFactory(person__user=cls.user_gf)
        EntityVersionFactory(entity=entity_manager.entity, parent=root)
        cls.user_other_gf = UserFactory()
        PartnershipEntityManagerFactory(person__user=cls.user_other_gf, entity=entity_manager.entity)

        # Partnership creation
        cls.date_ok = date.today() + timedelta(days=365)
        cls.partnership = PartnershipFactory()
        cls.partnership_gf = PartnershipFactory(
            author=cls.user_gf.person,
            ucl_entity=entity_manager.entity,
        )
        # Misc
        cls.url = reverse('partnerships:agreements:create', kwargs={'partnership_pk': cls.partnership.pk})
        cls.data = {
            'start_academic_year': AcademicYearFactory(year=cls.date_ok.year).pk,
            'end_academic_year': AcademicYearFactory(year=cls.date_ok.year + 1).pk,
            'status': AgreementStatus.WAITING.name,
            'comment': 'test',
            'media-name': 'test',
            'media-description': 'test',
            'media-url': 'http://example.com',
            'media-visibility': MediaVisibility.PUBLIC.name,
        }

    def test_get_view_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/agreements/create.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/agreements/create.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/agreements/create.html')

    def test_get_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/agreements/create.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_own_as_gf(self):
        self.client.force_login(self.user_gf)
        url = reverse('partnerships:agreements:create', kwargs={'partnership_pk': self.partnership_gf.pk})
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/agreements/create.html')

    def test_get_from_faculty_as_gf(self):
        self.client.force_login(self.user_other_gf)
        url = reverse('partnerships:agreements:create', kwargs={'partnership_pk': self.partnership_gf.pk})
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/agreements/create.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        data = self.data
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')
        self.assertEqual(len(mail.outbox), 0)

    def test_post_own_as_gf(self):
        self.client.force_login(self.user_gf)
        data = self.data.copy()
        del data['status']
        url = reverse('partnerships:agreements:create', kwargs={'partnership_pk': self.partnership_gf.pk})
        response = self.client.post(url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(str(self.user_gf), mail.outbox[0].body)
        mail.outbox = []

    def test_post_invalid_dates(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        data['start_academic_year'], data['end_academic_year'] = (
            # Flip the two
            data['end_academic_year'], data['start_academic_year']
        )
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTrue(response.context['form'].errors)


class PartnershipAgreementGeneralCreateViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(
            entity=entity_version.entity,
            person__user=cls.user_adri,
            scopes=[PartnershipType.GENERAL.name]
        )

        # Partnership creation
        cls.partnership = PartnershipFactory(
            partnership_type=PartnershipType.GENERAL.name,
        )

        # Misc
        cls.url = reverse('partnerships:agreements:create', kwargs={
            'partnership_pk': cls.partnership.pk,
        })
        cls.years = AcademicYearFactory.produce_in_future(date.today().year, 3)

        cls.data = {
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=365),
            'status': AgreementStatus.WAITING.name,
            'comment': 'test',
            'media-name': 'test',
            'media-description': 'test',
            'media-url': 'http://example.com',
            'media-visibility': MediaVisibility.PUBLIC.name,
        }

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/agreements/create.html')
        self.assertTrue('start_date' in response.context['form'].fields)

    def test_post(self):
        self.client.force_login(self.user_adri)
        response = self.client.post(self.url, self.data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')
        agreement = self.partnership.agreements.first()
        self.assertEqual(agreement.start_academic_year, self.years[0])

    def test_post_invalid_dates(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        data['start_date'] = data['end_date']
        data['end_date'] = date.today()
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTrue(response.context['form'].errors)


class PartnershipAgreementsUpdateViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # User creation
        cls.user = PartnershipEntityManagerFactory().person.user
        cls.user_adri = UserFactory()
        root = EntityVersionFactory(parent=None).entity
        entity_version = EntityVersionFactory(acronym='ADRI', parent=root)
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.user_gf = UserFactory()
        entity_manager = PartnershipEntityManagerFactory(person__user=cls.user_gf)
        EntityVersionFactory(entity=entity_manager.entity, parent=root)
        cls.user_other_gf = UserFactory()
        PartnershipEntityManagerFactory(person__user=cls.user_other_gf, entity=entity_manager.entity)

        # Partnership creation
        cls.date_ok = date.today() + timedelta(days=365)
        date_ko = date.today() - timedelta(days=365)
        cls.partnership = PartnershipFactory()
        PartnershipAgreementFactory(partnership=cls.partnership)
        cls.partnership_gf = PartnershipFactory(
            author=cls.user_gf.person,
            ucl_entity=entity_manager.entity,
        )
        PartnershipAgreementFactory(partnership=cls.partnership_gf)
        # Misc
        cls.url = reverse('partnerships:agreements:update', kwargs={
            'partnership_pk': cls.partnership.pk, 'pk': cls.partnership.agreements.all()[0].pk
        })
        cls.data = {
            'start_academic_year': AcademicYearFactory(year=cls.date_ok.year).pk,
            'end_academic_year': AcademicYearFactory(year=cls.date_ok.year + 1).pk,
            'status': AgreementStatus.WAITING.name,
            'comment': 'test',
            'media-name': 'test',
            'media-description': 'test',
            'media-url': 'http://example.com',
            'media-visibility': MediaVisibility.PUBLIC.name,
        }

    def test_get_view_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/agreements/update.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/agreements/update.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/agreements/update.html')

    def test_get_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/agreements/update.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_own_as_gf(self):
        self.client.force_login(self.user_gf)
        url = reverse('partnerships:agreements:update', kwargs={
            'partnership_pk': self.partnership_gf.pk, 'pk': self.partnership_gf.agreements.all()[0].pk
        })
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/agreements/update.html')

    def test_get_from_faculty_as_gf(self):
        self.client.force_login(self.user_other_gf)
        url = reverse('partnerships:agreements:update', kwargs={
            'partnership_pk': self.partnership_gf.pk, 'pk': self.partnership_gf.agreements.all()[0].pk
        })
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/agreements/update.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        data = self.data
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')

    def test_post_own_as_gf(self):
        self.client.force_login(self.user_gf)
        data = self.data
        url = reverse('partnerships:agreements:update', kwargs={
            'partnership_pk': self.partnership_gf.pk, 'pk': self.partnership_gf.agreements.all()[0].pk
        })
        response = self.client.post(url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')

    def test_post_validated_as_adri(self):
        self.client.force_login(self.user_adri)
        self.partnership.agreements.update(status=AgreementStatus.VALIDATED.name)
        data = self.data
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')

    def test_post_validated_as_gf(self):
        self.client.force_login(self.user_gf)
        self.partnership.agreements.update(status=AgreementStatus.VALIDATED.name)
        data = self.data
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/agreements/update.html')
        self.assertTemplateUsed(response, 'access_denied.html')


class PartnershipAgreementsDeleteViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # User creation
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.user_gf = UserFactory()
        entity_manager = PartnershipEntityManagerFactory(person__user=cls.user_gf)
        EntityVersionFactory(entity=entity_manager.entity)
        cls.user_other_gf = UserFactory()
        PartnershipEntityManagerFactory(person__user=cls.user_other_gf, entity=entity_manager.entity)

        # Partnership creation
        cls.date_ok = date.today() + timedelta(days=365)
        date_ko = date.today() - timedelta(days=365)
        cls.partnership = PartnershipFactory()
        PartnershipAgreementFactory(partnership=cls.partnership)
        cls.partnership_gf = PartnershipFactory(
            author=cls.user_gf.person,
            ucl_entity=entity_manager.entity,
        )
        PartnershipAgreementFactory(partnership=cls.partnership_gf)
        cls.partnership_out_of_date = PartnershipFactory(
            author=cls.user_gf.person,
            ucl_entity=entity_manager.entity,
        )
        PartnershipAgreementFactory(partnership=cls.partnership_out_of_date)
        # Misc
        cls.url = reverse('partnerships:agreements:delete', kwargs={
            'partnership_pk': cls.partnership.pk, 'pk': cls.partnership.agreements.all()[0].pk
        })

    def test_get_view_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/agreements/delete.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/agreements/delete.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/agreements/delete.html')

    def test_get_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/agreements/delete.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_own_as_gf(self):
        self.client.force_login(self.user_gf)
        url = reverse('partnerships:agreements:delete', kwargs={
            'partnership_pk': self.partnership_gf.pk, 'pk': self.partnership_gf.agreements.all()[0].pk
        })
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/agreements/delete.html')

    def test_get_from_faculty_as_gf(self):
        self.client.force_login(self.user_other_gf)
        url = reverse('partnerships:agreements:delete', kwargs={
            'partnership_pk': self.partnership_gf.pk, 'pk': self.partnership_gf.agreements.all()[0].pk
        })
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/agreements/delete.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        data = {}
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')

    def test_post_as_gf(self):
        self.client.force_login(self.user_adri)
        data = {}
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')

    def test_post_validated_as_adri(self):
        self.client.force_login(self.user_adri)
        self.partnership.agreements.update(status=AgreementStatus.VALIDATED.name)
        response = self.client.post(self.url, data={}, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/agreements/delete.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_post_validated_as_gf(self):
        self.client.force_login(self.user_gf)
        self.partnership.agreements.update(status=AgreementStatus.VALIDATED.name)
        response = self.client.post(self.url, data={}, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/agreements/delete.html')
        self.assertTemplateUsed(response, 'access_denied.html')
