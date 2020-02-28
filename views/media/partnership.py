from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, DeleteView
from .mixins import (
    PartnershipMediaFormMixin, PartnershipMediaMixin,
    MediaDownloadMixin,
)

__all__ = [
    'PartnershipMediaCreateView',
    'PartnershipMediaUpdateView',
    'PartnershipMediaDeleteView',
    'PartnershipMediaDownloadView',
]


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


class PartnershipMediaDownloadView(PartnershipMediaMixin, MediaDownloadMixin):
    pass
