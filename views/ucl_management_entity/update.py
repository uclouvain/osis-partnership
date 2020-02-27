from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import UpdateView

from partnership.forms import UCLManagementEntityForm
from partnership.models import UCLManagementEntity

__all__ = [
    'UCLManagementEntityUpdateView'
]


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
