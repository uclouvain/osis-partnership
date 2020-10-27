from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import UpdateView

from osis_role.contrib.views import PermissionRequiredMixin
from partnership.forms import PartnershipConfigurationForm
from partnership.models import PartnershipConfiguration

__all__ = [
    'PartnershipConfigurationUpdateView',
]


class PartnershipConfigurationUpdateView(PermissionRequiredMixin, UpdateView):
    form_class = PartnershipConfigurationForm
    template_name = 'partnerships/configuration_update.html'
    success_url = reverse_lazy('partnerships:list')
    login_url = 'access_denied'
    permission_required = 'partnership.change_partnershipconfiguration'

    def get_object(self, queryset=None):
        return PartnershipConfiguration.get_configuration()

    def form_valid(self, form):
        messages.success(self.request, _('configuration_saved'))
        return super().form_valid(form)
