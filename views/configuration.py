from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import UpdateView

from partnership.auth.predicates import is_linked_to_adri_entity
from partnership.forms import PartnershipConfigurationForm
from partnership.models import PartnershipConfiguration

__all__ = [
    'PartnershipConfigurationUpdateView',
]


class PartnershipConfigurationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    form_class = PartnershipConfigurationForm
    template_name = 'partnerships/configuration_update.html'
    success_url = reverse_lazy('partnerships:list')
    login_url = 'access_denied'

    def test_func(self):
        return is_linked_to_adri_entity(self.request.user)

    def get_object(self, queryset=None):
        return PartnershipConfiguration.get_configuration()

    def form_valid(self, form):
        messages.success(self.request, _('configuration_saved'))
        return super().form_valid(form)
