from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import DeleteView
from django.utils.translation import gettext_lazy as _

from osis_role.contrib.views import PermissionRequiredMixin
from partnership.models import Partnership

__all__ = [
    'PartnershipDeleteView',
]


class PartnershipDeleteView(PermissionRequiredMixin, DeleteView):
    model = Partnership
    template_name = 'partnerships/partnership/partnership_confirm_delete.html'
    permission_required = 'partnership.delete_partnership'
    login_url = 'access_denied'
    success_url = reverse_lazy('partnerships:list')

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.success(self.request, _('partnership_success_delete'))
        return response

