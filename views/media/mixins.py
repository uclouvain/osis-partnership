import os

from django.contrib import messages
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormMixin

from osis_common.decorators.download import set_download_cookie
from osis_role.contrib.views import PermissionRequiredMixin
from partnership.forms import MediaForm
from partnership.models import Partner
from partnership.views.partnership.mixins import PartnershipRelatedMixin


class PartnerMediaMixin(PermissionRequiredMixin):
    login_url = 'access_denied'
    permission_required = 'partnership.change_partner'

    def dispatch(self, request, *args, **kwargs):
        self.partner = get_object_or_404(Partner, pk=kwargs['partner_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_permission_object(self):
        return self.partner

    def get_queryset(self):
        return self.partner.medias.all()

    def get_success_url(self):
        return self.partner.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['partner'] = self.partner
        return context


class PartnerMediaFormMixin(PartnerMediaMixin, FormMixin):
    form_class = MediaForm
    login_url = 'access_denied'

    def get_template_names(self):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return 'partnerships/includes/media_form.html'
        return self.template_name

    def get_filename(self, filename):
        extension = filename.split('.')[-1]
        return 'partner_media_{}.{}'.format(self.partner.pk, extension)

    @transaction.atomic
    def form_valid(self, form):
        media = form.save(commit=False)
        if media.pk is None:
            media.author = self.request.user.person
        if media.file and not hasattr(form.cleaned_data['file'], 'path'):
            media.file.name = self.get_filename(media.file.name)
        media.save()
        form.save_m2m()
        self.partner.medias.add(media)
        messages.success(self.request, _('partner_media_saved'))
        return redirect(self.partner)

    def form_invalid(self, form):
        messages.error(self.request, _('partner_media_error'))
        return super().form_invalid(form)


class PartnershipMediaMixin(PartnershipRelatedMixin):
    def get_queryset(self):
        return self.partnership.medias.all()


class PartnershipMediaFormMixin(PartnershipMediaMixin, FormMixin):
    form_class = MediaForm
    login_url = 'access_denied'

    def get_template_names(self):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return 'partnerships/includes/media_form.html'
        return self.template_name

    def get_filename(self, filename):
        extension = filename.split('.')[-1]
        return 'partnership_media_{}.{}'.format(self.partnership.pk, extension)

    @transaction.atomic
    def form_valid(self, form):
        media = form.save(commit=False)
        if media.pk is None:
            media.author = self.request.user.person
        if media.file and not hasattr(form.cleaned_data['file'], 'path'):
            media.file.name = self.get_filename(media.file.name)
        media.save()
        form.save_m2m()
        self.partnership.medias.add(media)
        messages.success(self.request, _('partnership_media_saved'))
        return redirect(self.partnership)

    def form_invalid(self, form):
        messages.error(self.request, _('partnership_media_error'))
        return super().form_invalid(form)


class MediaDownloadMixin(SingleObjectMixin, View):
    @set_download_cookie
    def get(self, request, *args, **kwargs):
        media = self.get_object()
        if media.file is None:
            raise Http404
        response = FileResponse(media.file)
        response['Content-Disposition'] = 'attachment; filename={}'.format(
            os.path.basename(media.file.name)
        )
        return response
