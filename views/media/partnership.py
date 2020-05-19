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


class PartnershipMediaCreateView(PartnershipMediaFormMixin, CreateView):
    template_name = 'partnerships/medias/partnership_media_create.html'


class PartnershipMediaUpdateView(PartnershipMediaFormMixin, UpdateView):
    template_name = 'partnerships/medias/partnership_media_update.html'
    context_object_name = 'media'


class PartnershipMediaDeleteView(PartnershipMediaMixin, DeleteView):
    template_name = 'partnerships/medias/partnership_media_delete.html'

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/includes/media_delete.html'
        return self.template_name


class PartnershipMediaDownloadView(PartnershipMediaMixin, MediaDownloadMixin):
    pass
