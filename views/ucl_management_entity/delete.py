from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import DeleteView

from partnership import perms
from partnership.models import UCLManagementEntity

__all__ = [
    'UCLManagementEntityDeleteView'
]


class UCLManagementEntityDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = UCLManagementEntity
    template_name = "partnerships/ucl_management_entities/uclmanagemententity_delete.html"
    context_object_name = "ucl_management_entity"
    success_url = reverse_lazy('partnerships:ucl_management_entities:list')
    login_url = 'access_denied'

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/ucl_management_entities/includes/uclmanagemententity_delete_form.html'
        return self.template_name

    def test_func(self):
        return perms.user_can_delete_ucl_management_entity(self.request.user, self.get_object())
