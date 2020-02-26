from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView

from partnership.forms import UCLManagementEntityForm
from partnership.models import UCLManagementEntity

__all__ = [
    'UCLManagementEntityCreateView'
]


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
