import os

from django.http import FileResponse, Http404
from django.views import View
from django.views.generic.detail import SingleObjectMixin

from .mixins import PartnershipAgreementsMixin

__all__ = ['PartnershipAgreementMediaDownloadView']


class PartnershipAgreementMediaDownloadView(PartnershipAgreementsMixin, SingleObjectMixin, View):
    login_url = 'access_denied'

    def get(self, request, *args, **kwargs):
        agreement = self.get_object()
        media = agreement.media
        if media.file is None:
            raise Http404
        response = FileResponse(media.file)
        response['Content-Disposition'] = 'attachment; filename={}'.format(
            os.path.basename(media.file.name),
        )
        return response
