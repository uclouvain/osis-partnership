import codecs
import csv
import os
from datetime import date

from dal import autocomplete
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.db.models import (
    Exists, OuterRef, Prefetch, Q, Subquery
)
from django.http import (
    FileResponse, Http404, HttpResponse,
)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import ListView
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import (
    CreateView, DeleteView, FormMixin,
    ProcessFormView, UpdateView
)

from base.models.academic_year import (
    AcademicYear
)
from base.models.education_group_year import EducationGroupYear
from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.enums.entity_type import FACULTY
from base.models.person import Person
from partnership.forms import (
    ContactForm, FinancingFilterForm,
    FinancingImportForm, MediaForm, PartnershipAgreementForm,
    UCLManagementEntityForm,
)
from partnership.models import (
    Financing, Partner, PartnerEntity, Partnership,
    PartnershipAgreement, PartnershipConfiguration,
    UCLManagementEntity
)
from partnership.utils import academic_years, user_is_adri
from reference.models.country import Country

from .configuration import PartnershipConfigurationUpdateView
from .export import ExportView
from .partner import *
from .partnership import *
from .partnership.mixins import PartnershipListFilterMixin


class SimilarPartnerView(ListView, PermissionRequiredMixin):
    template_name = 'partnerships/partners/includes/similar_partners_preview.html'
    context_object_name = 'similar_partners'
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        search = self.request.GET.get('search', '')
        # Don't query for small searches
        if len(search) < 3:
            return Partner.objects.none()
        return Partner.objects.filter(name__icontains=search)[:10]


class PartnerMediaMixin(UserPassesTestMixin):
    login_url = 'access_denied'

    def dispatch(self, request, *args, **kwargs):
        self.partner = get_object_or_404(Partner, pk=kwargs['partner_pk'])
        return super(PartnerMediaMixin, self).dispatch(request, *args, **kwargs)

    def test_func(self):
        return self.partner.user_can_change(self.request.user)

    def get_queryset(self):
        return self.partner.medias.all()

    def get_success_url(self):
        return self.partner.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super(PartnerMediaMixin, self).get_context_data(**kwargs)
        context['partner'] = self.partner
        return context


class PartnerMediaFormMixin(PartnerMediaMixin, FormMixin):
    form_class = MediaForm
    login_url = 'access_denied'

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/includes/media_form.html'
        return self.template_name

    def get_filename(self, filename):
        extension = filename.split('.')[-1]
        return 'partner_media_{}.{}'.format(self.partner.pk, extension)

    @transaction.atomic
    def form_valid(self, form):
        media = form.save(commit=False)
        if media.pk is None:
            media.author = self.request.user
        if media.file and not hasattr(form.cleaned_data['file'], 'path'):
            media.file.name = self.get_filename(media.file.name)
        media.save()
        form.save_m2m()
        self.partner.medias.add(media)
        messages.success(self.request, _('partner_media_saved'))
        return redirect(self.partner)

    def form_invalid(self, form):
        messages.error(self.request, _('partner_media_error'))
        return super(PartnerMediaFormMixin, self).form_invalid(form)


class PartnerMediaCreateView(LoginRequiredMixin, PartnerMediaFormMixin, CreateView):
    template_name = 'partnerships/partners/medias/partner_media_create.html'
    login_url = 'access_denied'


class PartnerMediaUpdateView(LoginRequiredMixin, PartnerMediaFormMixin, UpdateView):
    template_name = 'partnerships/partners/medias/partner_media_update.html'
    context_object_name = 'media'
    login_url = 'access_denied'


class PartnerMediaDeleteView(LoginRequiredMixin, PartnerMediaMixin, DeleteView):
    template_name = 'partnerships/partners/medias/partner_media_delete.html'
    login_url = 'access_denied'

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/includes/media_delete.html'
        return self.template_name


class PartnerMediaDownloadView(PartnerMediaMixin, SingleObjectMixin, View):
    login_url = 'access_denied'

    def get(self, request, *args, **kwargs):
        media = self.get_object()
        if media.file is None:
            raise Http404
        response = FileResponse(media.file)
        response['Content-Disposition'] = 'attachment; filename={}'.format(os.path.basename(media.file.name))
        return response


class PartnershipContactMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = 'access_denied'

    def test_func(self):
        return self.partnership.user_can_change(self.request.user)

    def dispatch(self, request, *args, **kwargs):
        self.partnership = get_object_or_404(Partnership, pk=kwargs['partnership_pk'])
        return super(PartnershipContactMixin, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.partnership.contacts.all()

    def get_success_url(self):
        return self.partnership.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super(PartnershipContactMixin, self).get_context_data(**kwargs)
        context['partnership'] = self.partnership
        return context


class PartnershipContactFormMixin(PartnershipContactMixin, FormMixin):
    login_url = 'access_denied'
    form_class = ContactForm

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/contacts/includes/partnership_contact_form.html'
        return self.template_name

    def form_invalid(self, form):
        messages.error(self.request, _('partner_error'))
        return self.render_to_response(self.get_context_data(
            form=form,
        ))


class PartnershipContactCreateView(PartnershipContactFormMixin, CreateView):
    template_name = 'partnerships/contacts/partnership_contact_create.html'
    login_url = 'access_denied'

    def form_valid(self, form):
        contact = form.save()
        self.partnership.contacts.add(contact)
        messages.success(self.request, _("contact_creation_success"))
        return redirect(self.partnership)


class PartnershipContactUpdateView(PartnershipContactFormMixin, UpdateView):
    template_name = 'partnerships/contacts/partnership_contact_update.html'
    login_url = 'access_denied'

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _("contact_update_success"))
        return redirect(self.partnership)


class PartnershipContactDeleteView(PartnershipContactMixin, DeleteView):
    template_name = 'partnerships/contacts/contact_confirm_delete.html'
    login_url = 'access_denied'

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/contacts/includes/contact_delete_form.html'
        return self.template_name

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _("contact_delete_success"))
        return response


class PartnershipAgreementExportView(PermissionRequiredMixin, PartnershipListFilterMixin, ExportView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    @cached_property
    def is_agreements(self):
        return True

    def get_xls_headers(self):
        return [
            gettext('id'),
            gettext('partner'),
            gettext('country'),
            gettext('city'),
            gettext('partnership_supervisor'),
            gettext('faculty'),
            gettext('entity'),
            gettext('academic_years'),
            gettext('start_academic_year'),
            gettext('end_academic_year'),
            gettext('status'),
        ]

    def get_xls_data(self):
        queryset = self.get_queryset().prefetch_related(
            Prefetch(
                'partnership__ucl_university__entityversion_set',
                queryset=EntityVersion.objects.order_by('start_date'),
                to_attr='faculties',
            ),
        )
        for agreement in queryset:
            faculty = agreement.partnership.ucl_university.faculties[0]
            entity = agreement.partnership.ucl_university_labo
            years = academic_years(agreement.start_academic_year, agreement.end_academic_year)
            yield [
                agreement.pk,
                str(agreement.partnership.partner),
                str(agreement.partnership.partner.contact_address.country),
                str(agreement.partnership.partner.contact_address.city),
                str(agreement.partnership.supervisor),
                faculty.acronym,
                entity.most_recent_acronym if entity is not None else '',
                years,
                agreement.start_academic_year.year,
                agreement.end_academic_year.year + 1,
                agreement.get_status_display(),
            ]

    def get_description(self):
        return _('agreements')

    def get_filename(self):
        return now().strftime('agreements-%Y-%m-%d-%H-%M-%S')

    def get_title(self):
        return _('agreements')


class PartnershipMediaMixin(UserPassesTestMixin):
    login_url = 'access_denied'

    def dispatch(self, request, *args, **kwargs):
        self.partnership = get_object_or_404(Partnership, pk=kwargs['partnership_pk'])
        return super(PartnershipMediaMixin, self).dispatch(request, *args, **kwargs)

    def test_func(self):
        return self.partnership.user_can_change(self.request.user)

    def get_queryset(self):
        return self.partnership.medias.all()

    def get_success_url(self):
        return self.partnership.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super(PartnershipMediaMixin, self).get_context_data(**kwargs)
        context['partnership'] = self.partnership
        return context


class PartnershipMediaFormMixin(PartnershipMediaMixin, FormMixin):
    form_class = MediaForm
    login_url = 'access_denied'

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/includes/media_form.html'
        return self.template_name

    def get_filename(self, filename):
        extension = filename.split('.')[-1]
        return 'partnership_media_{}.{}'.format(self.partnership.pk, extension)

    @transaction.atomic
    def form_valid(self, form):
        media = form.save(commit=False)
        if media.pk is None:
            media.author = self.request.user
        if media.file and not hasattr(form.cleaned_data['file'], 'path'):
            media.file.name = self.get_filename(media.file.name)
        media.save()
        form.save_m2m()
        self.partnership.medias.add(media)
        messages.success(self.request, _('partnership_media_saved'))
        return redirect(self.partnership)

    def form_invalid(self, form):
        messages.error(self.request, _('partnership_media_error'))
        return super(PartnershipMediaFormMixin, self).form_invalid(form)


class PartnershipMediaCreateView(LoginRequiredMixin, PartnershipMediaFormMixin, CreateView):
    template_name = 'partnerships/medias/partnership_media_create.html'
    login_url = 'access_denied'


class PartnershipMediaUpdateView(LoginRequiredMixin, PartnershipMediaFormMixin, UpdateView):
    template_name = 'partnerships/medias/partnership_media_update.html'
    context_object_name = 'media'
    login_url = 'access_denied'


class PartnershipMediaDeleteView(LoginRequiredMixin, PartnershipMediaMixin, DeleteView):
    template_name = 'partnerships/medias/partnership_media_delete.html'
    login_url = 'access_denied'

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/includes/media_delete.html'
        return self.template_name


class PartnershipMediaDownloadView(PartnershipMediaMixin, SingleObjectMixin, View):
    login_url = 'access_denied'

    def get(self, request, *args, **kwargs):
        media = self.get_object()
        if media.file is None:
            raise Http404
        response = FileResponse(media.file)
        response['Content-Disposition'] = 'attachment; filename={}'.format(os.path.basename(media.file.name))
        return response


class PartnershipAgreementsMixin(LoginRequiredMixin, UserPassesTestMixin):
    context_object_name = 'agreement'
    login_url = 'access_denied'

    def dispatch(self, request, *args, **kwargs):
        self.partnership = get_object_or_404(Partnership, pk=kwargs['partnership_pk'])
        return super(PartnershipAgreementsMixin, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.partnership.agreements.all()

    def get_success_url(self):
        return self.partnership.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super(PartnershipAgreementsMixin, self).get_context_data(**kwargs)
        context['partnership'] = self.partnership
        return context


class PartnershipAgreementsFormMixin(PartnershipAgreementsMixin):
    form_class = PartnershipAgreementForm
    login_url = 'access_denied'

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/includes/partnership_agreement_form.html'
        return self.template_name

    def get_form_kwargs(self):
        kwargs = super(PartnershipAgreementsFormMixin, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_form_media(self):
        kwargs = self.get_form_kwargs()
        kwargs['prefix'] = 'media'
        if self.object is not None:
            kwargs['instance'] = self.object.media
        del kwargs['user']
        form = MediaForm(**kwargs)
        del form.fields['type']
        return form

    def get_context_data(self, **kwargs):
        if 'form_media' not in kwargs:
            kwargs['form_media'] = self.get_form_media()
        return super(PartnershipAgreementsFormMixin, self).get_context_data(**kwargs)

    def check_dates(self, agreement):
        if agreement.start_academic_year.year < self.partnership.start_academic_year.year:
            messages.warning(self.request, _('partnership_agreement_warning_before'))
        if agreement.end_academic_year.year > self.partnership.end_academic_year.year:
            messages.warning(self.request, _('partnership_agreement_warning_after'))

    def get_filename(self, filename):
        extension = filename.split('.')[-1]
        return 'partnership_agreement_{}_{}.{}'.format(self.partnership.pk, self.partnership.partner.pk, extension)

    def form_invalid(self, form, form_media):
        messages.error(self.request, _('partnership_agreement_error'))
        return self.render_to_response(self.get_context_data(form=form, form_media=form_media))

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        form_media = self.get_form_media()
        # Do the valid before to ensure the errors are calculated
        form_media_valid = form_media.is_valid()
        if form.is_valid() and form_media_valid:
            return self.form_valid(form, form_media)
        else:
            return self.form_invalid(form, form_media)


class PartneshipAgreementCreateView(PartnershipAgreementsFormMixin, CreateView):
    template_name = 'partnerships/agreements/create.html'
    login_url = 'access_denied'

    def test_func(self):
        return self.partnership.user_can_change(self.request.user)

    @transaction.atomic
    def form_valid(self, form, form_media):
        media = form_media.save(commit=False)
        media.author = self.request.user
        if media.file:
            media.file.name = self.get_filename(media.file.name)
        media.save()
        form_media.save_m2m()
        agreement = form.save(commit=False)
        agreement.partnership = self.partnership
        agreement.media = media
        agreement.save()
        form.save_m2m()
        self.check_dates(agreement)
        messages.success(self.request, _('partnership_agreement_success'))
        return redirect(self.partnership)

    def post(self, request, *args, **kwargs):
        self.object = None
        return super(PartneshipAgreementCreateView, self).post(request, *args, **kwargs)


class PartneshipAgreementUpdateView(PartnershipAgreementsFormMixin, UpdateView):
    template_name = 'partnerships/agreements/update.html'
    login_url = 'access_denied'

    def test_func(self):
        return self.get_object().user_can_change(self.request.user)

    def get_queryset(self):
        return PartnershipAgreement.objects.select_related('start_academic_year', 'end_academic_year')

    @transaction.atomic
    def form_valid(self, form, form_media):
        media = form_media.save(commit=False)
        if media.file and not hasattr(form_media.cleaned_data['file'], 'path'):
            media.file.name = self.get_filename(media.file.name)
        media.save()
        form_media.save_m2m()
        agreement = form.save()
        self.check_dates(agreement)
        messages.success(self.request, _('partnership_agreement_success'))
        return redirect(self.partnership)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(PartneshipAgreementUpdateView, self).post(request, *args, **kwargs)


class PartneshipAgreementDeleteView(PartnershipAgreementsMixin, DeleteView):
    template_name = 'partnerships/agreements/delete.html'
    login_url = 'access_denied'

    def test_func(self):
        return self.get_object().user_can_delete(self.request.user)

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/agreements/includes/delete.html'
        return self.template_name


class PartnershipAgreementMediaDownloadView(PartnershipAgreementsMixin, SingleObjectMixin, View):
    login_url = 'access_denied'

    def test_func(self):
        return self.partnership.user_can_change(self.request.user)

    def get(self, request, *args, **kwargs):
        agreement = self.get_object()
        media = agreement.media
        if media.file is None:
            raise Http404
        response = FileResponse(media.file)
        response['Content-Disposition'] = 'attachment; filename={}'.format(os.path.basename(media.file.name))
        return response


# UCLManagementEntities views :

class UCLManagementEntityListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = UCLManagementEntity
    template_name = "partnerships/ucl_management_entities/uclmanagemententity_list.html"
    context_object_name = "ucl_management_entities"
    login_url = 'access_denied'

    def test_func(self):
        result = UCLManagementEntity.user_can_list(self.request.user)
        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_create_ucl_management_entity'] = UCLManagementEntity.user_can_create(self.request.user)
        return context

    def get_queryset(self):
        queryset = (
            UCLManagementEntity.objects
            .annotate(
                faculty_most_recent_acronym=Subquery(
                    EntityVersion.objects
                        .filter(entity=OuterRef('faculty__pk'))
                        .order_by('-start_date')
                        .values('acronym')[:1]
                ),
                entity_most_recent_acronym=Subquery(
                    EntityVersion.objects
                        .filter(entity=OuterRef('entity__pk'))
                        .order_by('-start_date')
                        .values('acronym')[:1]
                ),
            )
            .order_by('faculty_most_recent_acronym', 'entity_most_recent_acronym')
            .select_related('academic_responsible', 'administrative_responsible')
        )
        if not user_is_adri(self.request.user):
            queryset = queryset.filter(
                Q(faculty__partnershipentitymanager__person__user=self.request.user)
                | Q(faculty__entityversion__parent__partnershipentitymanager__person__user=self.request.user)
            )
        return queryset.distinct()


class UCLManagementEntityCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = UCLManagementEntity
    template_name = "partnerships/ucl_management_entities/uclmanagemententity_create.html"
    form_class = UCLManagementEntityForm
    success_url = reverse_lazy('partnerships:ucl_management_entities:list')
    login_url = 'access_denied'

    def test_func(self):
        result = UCLManagementEntity.user_can_create(self.request.user)
        return result

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _('ucl_management_entity_create_success'))
        return super().form_valid(form)


class UCLManagementEntityUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = UCLManagementEntity
    template_name = "partnerships/ucl_management_entities/uclmanagemententity_update.html"
    form_class = UCLManagementEntityForm
    context_object_name = "ucl_management_entity"
    success_url = reverse_lazy('partnerships:ucl_management_entities:list')
    login_url = 'access_denied'

    def test_func(self):
        self.object = self.get_object()
        result = self.object.user_can_change(self.request.user)
        return result

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _('ucl_management_entity_change_success'))
        return super().form_valid(form)


class UCLManagementEntityDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = UCLManagementEntity
    template_name = "partnerships/ucl_management_entities/uclmanagemententity_delete.html"
    context_object_name = "ucl_management_entity"
    success_url = reverse_lazy('partnerships:ucl_management_entities:list')
    login_url = 'access_denied'

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/ucl_management_entities/includes/uclmanagemententity_delete_form.html'
        return self.template_name

    def test_func(self):
        return self.get_object().user_can_delete(self.request.user)


# Financing views :


class FinancingExportView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = 'access_denied'

    def test_func(self):
        return user_is_adri(self.request.user)

    def get_csv_data(self, academic_year):
        countries = Country.objects.all().order_by('name').prefetch_related(
            Prefetch(
                'financing_set',
                queryset=Financing.objects.prefetch_related(
                    'academic_year'
                ).filter(academic_year=academic_year)
            )
        )
        for country in countries:
            if country.financing_set.all():
                for financing in country.financing_set.all():
                    row = {
                        'country': country.iso_code,
                        'name': financing.name,
                        'url': financing.url,
                        'country_name': country.name,
                    }
                    yield row
            else:
                row = {
                    'country': country.iso_code,
                    'name': '',
                    'url': '',
                    'country_name': country.name,
                }
                yield row

    def get(self, *args, year=None, **kwargs):
        if year is None:
            configuration = PartnershipConfiguration.get_configuration()
            self.academic_year = configuration.get_current_academic_year_for_creation_modification()
        else:
            self.academic_year = get_object_or_404(AcademicYear, year=year)

        filename = "financings_{}".format(self.academic_year)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(filename)

        fieldnames = ['country_name', 'country', 'name', 'url']
        wr = csv.DictWriter(response, delimiter=';', quoting=csv.QUOTE_NONE, fieldnames=fieldnames)
        wr.writeheader()
        for row in self.get_csv_data(academic_year=self.academic_year):
            wr.writerow(row)
        return response


class FinancingImportView(LoginRequiredMixin, UserPassesTestMixin, TemplateResponseMixin, FormMixin, ProcessFormView):
    form_class = FinancingImportForm
    template_name = "partnerships/financings/financing_import.html"
    login_url = 'access_denied'

    def test_func(self):
        return user_is_adri(self.request.user)

    def get_success_url(self, academic_year=None):
        if academic_year is None:
            configuration = PartnershipConfiguration.get_configuration()
            academic_year = configuration.get_current_academic_year_for_creation_modification()
        return reverse('partnerships:financings:list', kwargs={'year': academic_year.year})

    def get_reader(self, csv_file):
        sample = csv_file.read(1024).decode('utf8')
        dialect = csv.Sniffer().sniff(sample)
        csv_file.seek(0)
        reader = csv.DictReader(
            codecs.iterdecode(csv_file, 'utf8'),
            fieldnames=['country_name', 'country', 'name', 'url'],
            dialect=dialect,
        )
        return reader

    def handle_csv(self, reader):
        url_validator = URLValidator()
        financings_countries = {}
        financings_url = {}
        next(reader, None)
        for row in reader:
            if not row['name']:
                continue
            try:
                country = Country.objects.get(iso_code=row['country'])
            except Country.DoesNotExist:
                messages.warning(
                    self.request, _('financing_country_not_imported_{country}').format(country=row['country']))
                continue
            if row['name'] not in financings_url:
                url = row['url']
                try:
                    if url:
                        url_validator(url)
                    financings_url[row['name']] = url
                except ValidationError:
                    financings_url[row['name']] = ''
                    messages.warning(
                        self.request, _('financing_url_invalid_{country}_{url}').format(country=country, url=url))
            financings_countries.setdefault(row['name'], []).append(country)
        return financings_countries, financings_url

    @transaction.atomic
    def update_financings(self, academic_year, financings_countries, financings_url):
        Financing.objects.filter(academic_year=academic_year).delete()
        financings = []
        for name in financings_countries.keys():
            financings.append(
                Financing(
                    academic_year=academic_year,
                    name=name,
                    url=financings_url.get(name, None)
                )
            )
        financings = Financing.objects.bulk_create(financings)
        for financing in financings:
            financing.countries.set(financings_countries.get(financing.name, []))

    def form_valid(self, form):
        academic_year = form.cleaned_data.get('import_academic_year')

        reader = self.get_reader(self.request.FILES['csv_file'])
        try:
            financings_countries, financings_url = self.handle_csv(reader)
        except ValueError:
            messages.error(self.request, _('financings_imported_error'))
            return redirect(self.get_success_url(academic_year))

        self.update_financings(academic_year, financings_countries, financings_url)

        messages.success(self.request, _('financings_imported'))
        return redirect(self.get_success_url(academic_year))


class FinancingListView(LoginRequiredMixin, UserPassesTestMixin, FormMixin, ListView):
    model = Country
    template_name = "partnerships/financings/financing_list.html"
    form_class = FinancingFilterForm
    context_object_name = "countries"
    paginate_by = 25
    paginate_orphans = 2
    paginate_neighbours = 3
    login_url = 'access_denied'

    def test_func(self):
        return user_is_adri(self.request.user)

    def dispatch(self, *args, year=None, **kwargs):
        if year is None:
            configuration = PartnershipConfiguration.get_configuration()
            self.academic_year = configuration.get_current_academic_year_for_creation_modification()
        else:
            self.academic_year = get_object_or_404(AcademicYear, year=year)

        if self.request.method == "POST":
            self.import_form = FinancingImportForm(self.request.POST, self.request.FILES)
            self.form = FinancingFilterForm(self.request.POST)
        else:
            self.import_form = FinancingImportForm(initial={'import_academic_year': self.academic_year})
            self.form = FinancingFilterForm(initial={'year': self.academic_year})
        return super().dispatch(*args, **kwargs)

    def get_ordering(self):
        ordering = self.request.GET.get('ordering', None)
        if ordering == 'financing_name':
            return [
                'financing_name',
                'name',
            ]
        elif ordering == '-financing_name':
            return [
                '-financing_name',
                'name',
            ]
        elif ordering == 'financing_url':
            return [
                'financing_url',
                'name',
            ]
        elif ordering == '-financing_url':
            return [
                '-financing_url',
                'name',
            ]
        elif ordering == '-name':
            return [
                '-name',
                'iso_code',
            ]
        else:
            return [
                'name',
                'iso_code'
            ]

    def post(self, *args, **kwargs):
        if self.form.is_valid():
            return self.form_valid(self.form)
        return self.form_invalid(self.form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['import_form'] = self.import_form
        context['paginate_neighbours'] = self.paginate_neighbours
        context['can_import_financing'] = Financing.user_can_import(self.request.user)
        context['can_export_financing'] = Financing.user_can_export(self.request.user)
        context['academic_year'] = self.academic_year
        return context

    def get_success_url(self):
        return reverse('partnerships:financings:list', kwargs={'year': self.academic_year.year})

    def get_queryset(self):
        queryset = (
            Country.objects
            .annotate(
                financing_name=Subquery(
                    Financing.objects
                        .filter(countries=OuterRef('pk'), academic_year=self.academic_year)
                        .values('name')[:1]
                ),
                financing_url=Subquery(
                    Financing.objects
                        .filter(countries=OuterRef('pk'), academic_year=self.academic_year)
                        .values('url')[:1]
                ),
            )
            .order_by(*self.get_ordering())
            .distinct()
        )
        return queryset

    def form_valid(self, form):
        self.academic_year = form.cleaned_data.get('year', None)
        if self.academic_year is None:
            configuration = PartnershipConfiguration.get_configuration()
            self.academic_year = configuration.get_current_academic_year_for_creation_modification()
        return redirect(self.get_success_url())


# Autocompletes


class PersonAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = Person.objects.filter(employee=True)
        if self.q:
            qs = qs.filter(
                Q(first_name__icontains=self.q) |
                Q(middle_name__icontains=self.q) |
                Q(last_name__icontains=self.q)
            )
        return qs.distinct()

    def get_result_label(self, person):
        return '{0} - {1}'.format(person, person.email)


class EntityAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = Entity.objects.prefetch_related('entityversion_set').all()
        if self.q:
            qs = qs.filter(
                entityversion__acronym__icontains=self.q
            )
        return qs.distinct()


class PartnershipAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = Partnership.objects.all()
        if self.q:
            qs = qs.filter(
                Q(partner__name__icontains=self.q)
                | Q(partner_entity__name__icontains=self.q)
            )
        return qs.distinct()


class PartnerAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_results(self, context):
        """Return data for the 'results' key of the response."""
        return [
            {
                'id': self.get_result_value(result),
                'text': self.get_result_label(result),
                'pic_code': result.pic_code,
                'erasmus_code': result.erasmus_code,
            } for result in context['object_list']
        ]

    def get_queryset(self):
        qs = Partner.objects.all()
        pk = self.forwarded.get('partner_pk', None)
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        qs = qs.distinct()
        if pk is not None:
            current = Partner.objects.get(pk=pk)
            return [current] + list(filter(lambda x: x.is_actif, qs))
        return list(filter(lambda x: x.is_actif, qs))


class PartnerEntityAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = PartnerEntity.objects.all()
        partner = self.forwarded.get('partner', None)
        if partner:
            qs = qs.filter(partner=partner)
        else:
            return PartnerEntity.objects.none()
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs.distinct()


class FacultyAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = (
            Entity.objects
                .annotate(
                    most_recent_acronym=Subquery(
                        EntityVersion.objects
                            .filter(entity=OuterRef('pk'))
                            .order_by('-start_date')
                            .values('acronym')[:1]
                    ),
                )
                .filter(entityversion__entity_type=FACULTY)
        )
        if not user_is_adri(self.request.user):
            qs = qs.filter(
                Q(partnershipentitymanager__person__user=self.request.user)
                | Q(entityversion__parent__partnershipentitymanager__person__user=self.request.user)
            )
        if self.q:
            qs = qs.filter(most_recent_acronym__icontains=self.q)
        qs = qs.order_by('most_recent_acronym')
        return qs.distinct()

    def get_result_label(self, result):
        if result.entityversion_set:
            title = result.entityversion_set.latest("start_date").title
        else:
            return result.most_recent_acronym
        return '{0.most_recent_acronym} - {1}'.format(result, title)


class FacultyEntityAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = Entity.objects.annotate(
            most_recent_acronym=Subquery(
                EntityVersion.objects
                    .filter(entity=OuterRef('pk'))
                    .order_by('-start_date')
                    .values('acronym')[:1]
            ),
        )
        ucl_university = self.forwarded.get('ucl_university', None)
        if ucl_university:
            qs = qs.filter(entityversion__parent=ucl_university)
        else:
            return Entity.objects.none()
        qs = qs.annotate(
            is_valid=Exists(
                EntityVersion.objects
                    .filter(entity=OuterRef('pk'))
                    .exclude(end_date__lte=date.today())
            )
        ).filter(is_valid=True)
        if self.q:
            qs = qs.filter(most_recent_acronym__icontains=self.q)
        qs = qs.order_by('most_recent_acronym')
        return qs.distinct()

    def get_result_label(self, result):
        title = result.entityversion_set.latest("start_date").title
        return '{0.most_recent_acronym} - {1}'.format(result, title)


class UclUniversityAutocompleteView(FacultyAutocompleteView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        queryset = super(UclUniversityAutocompleteView, self).get_queryset()
        queryset = queryset.filter(faculty_managements__isnull=False)
        return queryset


class UclUniversityLaboAutocompleteView(FacultyEntityAutocompleteView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        queryset = super(UclUniversityLaboAutocompleteView, self).get_queryset()
        queryset = queryset.filter(entity_managements__isnull=False)
        return queryset


class PartnershipYearEntitiesAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        faculty = self.forwarded.get('faculty', None)
        if faculty is not None:
            qs = Entity.objects.annotate(
                most_recent_acronym=Subquery(
                    EntityVersion.objects
                        .filter(entity=OuterRef('pk'))
                        .order_by('-start_date')
                        .values('acronym')[:1]
                ),
            ).filter(entityversion__parent=faculty)
        else:
            return Entity.objects.none()
        qs = qs.annotate(
            is_valid=Exists(
                EntityVersion.objects
                .filter(entity=OuterRef('pk'))
                .exclude(end_date__lte=date.today())
            )
        ).filter(is_valid=True)
        if self.q:
            qs = qs.filter(most_recent_acronym__icontains=self.q)
        return qs.distinct()

    def get_result_label(self, result):
        try:
            title = result.entityversion_set.latest("start_date").title
            return '{0.most_recent_acronym} - {1}'.format(result, title)
        except EntityVersion.DoesNotExist:
            return result.most_recent_acronym


class PartnershipYearOffersAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = EducationGroupYear.objects.filter(joint_diploma=True).select_related('academic_year')
        next_academic_year = \
            PartnershipConfiguration.get_configuration().get_current_academic_year_for_creation_modification()
        qs = qs.filter(academic_year=next_academic_year)
        # Education levels filter
        education_levels = self.forwarded.get('education_levels', None)
        if education_levels is not None:
            qs = qs.filter(education_group_type__partnership_education_levels__in=education_levels)
        else:
            return EducationGroupYear.objects.none()
        # Entities filter
        entities = self.forwarded.get('entities', None)
        if entities is not None:
            qs = qs.filter(Q(management_entity__in=entities) | Q(administration_entity__in=entities))
        else:
            faculty = self.forwarded.get('faculty', None)
            if faculty is not None:
                qs = qs.filter(
                    Q(management_entity=faculty) | Q(administration_entity=faculty)
                    | Q(management_entity__entityversion__parent=faculty)
                    | Q(administration_entity__entityversion__parent=faculty)
                )
            else:
                return EducationGroupYear.objects.none()
        # Query filter
        if self.q:
            qs = qs.filter(title__icontains=self.q)
        return qs.distinct('education_group').order_by()

    def get_result_label(self, result):
        return '{0.acronym} - {0.title}'.format(result)


# Partnership filters autocompletes

class PartnerAutocompletePartnershipsFilterView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = Partner.objects.filter(partnerships__isnull=False)
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs.distinct()


class PartnerEntityAutocompletePartnershipsFilterView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = PartnerEntity.objects.filter(partnerships__isnull=False)
        partner = self.forwarded.get('partner', None)
        if partner:
            qs = qs.filter(partner=partner)
        else:
            return PartnerEntity.objects.none()
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs.distinct()


class UclUniversityAutocompleteFilterView(UclUniversityAutocompleteView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = (
            Entity.objects
            .annotate(
                most_recent_acronym=Subquery(
                    EntityVersion.objects
                        .filter(entity=OuterRef('pk'))
                        .order_by('-start_date')
                        .values('acronym')[:1]
                ),
                is_valid=Exists(
                    EntityVersion.objects
                        .filter(entity=OuterRef('pk'))
                        .exclude(end_date__lte=date.today())
                ),
            )
            .filter(partnerships__isnull=False, is_valid=True)
        )
        if self.q:
            qs = qs.filter(most_recent_acronym__icontains=self.q)
        qs = qs.order_by('most_recent_acronym')
        return qs.distinct()


class UclUniversityLaboAutocompleteFilterView(UclUniversityLaboAutocompleteView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = super().get_queryset()
        ucl_university = self.forwarded.get('ucl_university', None)
        if ucl_university:
            qs = qs.filter(partnerships_labo__ucl_university=ucl_university)
        else:
            return Entity.objects.none()
        return qs.distinct()


class YearsEntityAutocompleteFilterView(FacultyEntityAutocompleteView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = super(YearsEntityAutocompleteFilterView, self).get_queryset()
        qs = qs.filter(partnerships_years__isnull=False)
        return qs


class UniversityOffersAutocompleteFilterView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = EducationGroupYear.objects.all().select_related('academic_year')
        next_academic_year = \
            PartnershipConfiguration.get_configuration().get_current_academic_year_for_creation_modification()
        qs = qs.filter(academic_year=next_academic_year)
        ucl_university = self.forwarded.get('ucl_university', None)
        education_level = self.forwarded.get('education_level', None)
        entity = self.forwarded.get('years_entity', None)
        if not ucl_university or not education_level:
            return EducationGroupYear.objects.none()
        if entity:
            qs = qs.filter(partnerships__entities=entity)
        else:
            qs = qs.filter(partnerships__partnership__ucl_university=ucl_university)
        qs = qs.filter(education_group_type__partnership_education_levels=education_level)
        if self.q:
            qs = qs.filter(title__icontains=self.q)
        return qs.distinct()

    def get_result_label(self, result):
        return '{0.acronym} - {0.title}'.format(result)
