from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, DeleteView

from .mixins import (
    PartnerMediaFormMixin,
    PartnerMediaMixin,
    MediaDownloadMixin,
)

__all__ = [
    'PartnerMediaCreateView',
    'PartnerMediaUpdateView',
    'PartnerMediaDeleteView',
    'PartnerMediaDownloadView',
]


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
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return 'partnerships/includes/media_delete.html'
        return self.template_name


class PartnerMediaDownloadView(PartnerMediaMixin, MediaDownloadMixin):
    pass
