from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from base.tests.factories.user import UserFactory
from partnership.tests.factories import PartnerFactory


class PartnersListViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        for i in range(21):
            PartnerFactory(is_ies=False)
        cls.partner_erasmus_last = PartnerFactory(erasmus_code='ZZZ', is_ies=False)
        cls.partner_name = PartnerFactory(name='foobar', is_ies=False)
        cls.partner_partner_type = PartnerFactory(is_ies=False)
        cls.partner_pic_code = PartnerFactory(pic_code='foobar', is_ies=False)
        cls.partner_erasmus_code = PartnerFactory(erasmus_code='foobar', is_ies=False)
        cls.partner_is_ies = PartnerFactory(is_ies=True)
        cls.partner_is_valid = PartnerFactory(is_valid=False, is_ies=False)
        cls.partner_is_actif = PartnerFactory(
            end_date=timezone.now() - timedelta(days=1),
            is_ies=False
        )
        cls.partner_tags = PartnerFactory(is_ies=False)
        cls.user = UserFactory()
        cls.url = reverse('partnerships:partners:list')

    def test_get_list_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/partners_list.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_list_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partners/partners_list.html')

    def test_get_list_pagination(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?page=2')
        self.assertTemplateUsed(response, 'partnerships/partners/partners_list.html')
        context = response.context_data
        self.assertEqual(len(context['partners']), 10)

    def test_get_list_ordering(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?ordering=-erasmus_code')
        self.assertTemplateUsed(response, 'partnerships/partners/partners_list.html')
        context = response.context_data
        self.assertEqual(context['partners'][0], self.partner_erasmus_last)

    def test_filter_name(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?name=foo')
        self.assertTemplateUsed(response, 'partnerships/partners/partners_list.html')
        context = response.context_data
        self.assertEqual(len(context['partners']), 1)
        self.assertEqual(context['partners'][0], self.partner_name)

    def test_filter_partner_type(self):
        self.client.force_login(self.user)
        url = self.url + '?partner_type={0}'.format(self.partner_partner_type.partner_type.id)
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'partnerships/partners/partners_list.html')
        context = response.context_data
        self.assertEqual(len(context['partners']), 1)
        self.assertEqual(context['partners'][0], self.partner_partner_type)

    def test_filter_pic_code(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?pic_code=foo')
        self.assertTemplateUsed(response, 'partnerships/partners/partners_list.html')
        context = response.context_data
        self.assertEqual(len(context['partners']), 1)
        self.assertEqual(context['partners'][0], self.partner_pic_code)

    def test_filter_erasmus_code(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?erasmus_code=foo')
        self.assertTemplateUsed(response, 'partnerships/partners/partners_list.html')
        context = response.context_data
        self.assertEqual(len(context['partners']), 1)
        self.assertEqual(context['partners'][0], self.partner_erasmus_code)

    def test_filter_is_ies(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?is_ies=True')
        self.assertTemplateUsed(response, 'partnerships/partners/partners_list.html')
        context = response.context_data
        self.assertEqual(len(context['partners']), 1)
        self.assertEqual(context['partners'][0], self.partner_is_ies)

    def test_filter_is_valid(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?is_valid=False')
        self.assertTemplateUsed(response, 'partnerships/partners/partners_list.html')
        context = response.context_data
        self.assertEqual(len(context['partners']), 1)
        self.assertEqual(context['partners'][0], self.partner_is_valid)

    def test_filter_is_actif(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?is_actif=False')
        self.assertTemplateUsed(response, 'partnerships/partners/partners_list.html')
        context = response.context_data
        self.assertEqual(len(context['partners']), 1)
        self.assertEqual(context['partners'][0], self.partner_is_actif)

    def test_filter_tags(self):
        self.client.force_login(self.user)
        url = self.url + '?tags={0}'.format(self.partner_tags.tags.all().first().id)
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'partnerships/partners/partners_list.html')
        context = response.context_data
        self.assertEqual(len(context['partners']), 1)
        self.assertEqual(context['partners'][0], self.partner_tags)


class PartnersExportViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        for i in range(21):
            PartnerFactory(is_ies=False)
        cls.partner_erasmus_last = PartnerFactory(erasmus_code='ZZZ', is_ies=False)
        cls.partner_name = PartnerFactory(name='foobar', is_ies=False)
        cls.partner_partner_type = PartnerFactory(is_ies=False)
        cls.partner_pic_code = PartnerFactory(pic_code='foobar', is_ies=False)
        cls.partner_erasmus_code = PartnerFactory(erasmus_code='foobar', is_ies=False)
        cls.partner_is_ies = PartnerFactory(is_ies=True)
        cls.partner_is_valid = PartnerFactory(is_valid=False, is_ies=False)
        cls.partner_is_actif = PartnerFactory(
            end_date=timezone.now() - timedelta(days=1),
            is_ies=False
        )
        cls.partner_tags = PartnerFactory(is_ies=False)
        cls.user = UserFactory()
        cls.url = reverse('partnerships:partners:export')

    def test_get_list_anonymous(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_get_list_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
