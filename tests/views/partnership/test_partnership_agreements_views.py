from datetime import date, timedelta

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory
from partnership.models import AgreementStatus, MediaVisibility
from partnership.tests.factories import (
    PartnershipAgreementFactory,
    PartnershipEntityManagerFactory,
    PartnershipFactory
)


class PartnershipsListViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        for i in range(15):
            PartnershipAgreementFactory()
        cls.user = UserFactory()
        cls.user_adri = UserFactory()

        cls.user.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))
        cls.user_adri.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))

        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.url = reverse('partnerships:list') + '?agreements=1'

    def test_get_list_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnership/partnership_list.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_list_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        self.assertTemplateNotUsed(response, 'partnerships/agreements/includes/agreements_list_results.html')

    def test_get_list_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        self.assertTemplateUsed(response, 'partnerships/agreements/includes/agreements_list_results.html')


class PartnershipAgreementCreateViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # User creation
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.user_gf = UserFactory()
        entity_manager = PartnershipEntityManagerFactory(person__user=cls.user_gf)
        cls.user_other_gf = UserFactory()
        PartnershipEntityManagerFactory(person__user=cls.user_other_gf, entity=entity_manager.entity)

        cls.user.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))
        cls.user_adri.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))
        cls.user_gf.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))
        cls.user_other_gf.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))

        # Partnership creation
        cls.date_ok = date.today() + timedelta(days=365)
        cls.partnership = PartnershipFactory()
        cls.partnership_gf = PartnershipFactory(author=cls.user_gf.person, ucl_university=entity_manager.entity)
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

    def test_post_own_as_gf(self):
        self.client.force_login(self.user_gf)
        data = self.data.copy()
        del data['status']
        url = reverse('partnerships:agreements:create', kwargs={'partnership_pk': self.partnership_gf.pk})
        response = self.client.post(url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')


class PartnershipAgreementsUpdateViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # User creation
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.user_gf = UserFactory()
        entity_manager = PartnershipEntityManagerFactory(person__user=cls.user_gf)
        cls.user_other_gf = UserFactory()
        PartnershipEntityManagerFactory(person__user=cls.user_other_gf, entity=entity_manager.entity)

        cls.user.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))
        cls.user_adri.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))
        cls.user_gf.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))
        cls.user_other_gf.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))

        # Partnership creation
        cls.date_ok = date.today() + timedelta(days=365)
        date_ko = date.today() - timedelta(days=365)
        cls.partnership = PartnershipFactory()
        PartnershipAgreementFactory(partnership=cls.partnership)
        cls.partnership_gf = PartnershipFactory(author=cls.user_gf.person, ucl_university=entity_manager.entity)
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
        cls.user_other_gf = UserFactory()
        PartnershipEntityManagerFactory(person__user=cls.user_other_gf, entity=entity_manager.entity)

        cls.user.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))
        cls.user_adri.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))
        cls.user_gf.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))
        cls.user_other_gf.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))

        # Partnership creation
        cls.date_ok = date.today() + timedelta(days=365)
        date_ko = date.today() - timedelta(days=365)
        cls.partnership = PartnershipFactory()
        PartnershipAgreementFactory(partnership=cls.partnership)
        cls.partnership_gf = PartnershipFactory(author=cls.user_gf.person, ucl_university=entity_manager.entity)
        PartnershipAgreementFactory(partnership=cls.partnership_gf)
        cls.partnership_out_of_date = PartnershipFactory(author=cls.user_gf.person, ucl_university=entity_manager.entity)
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