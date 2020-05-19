from django.urls import reverse_lazy
from django.views.generic import DeleteView

from osis_role.contrib.views import PermissionRequiredMixin
from partnership.models import UCLManagementEntity

__all__ = [
    'UCLManagementEntityDeleteView'
]


class UCLManagementEntityDeleteView(PermissionRequiredMixin, DeleteView):
    model = UCLManagementEntity
    template_name = "partnerships/ucl_management_entities/uclmanagemententity_delete.html"
    context_object_name = "ucl_management_entity"
    success_url = reverse_lazy('partnerships:ucl_management_entities:list')
    login_url = 'access_denied'
    permission_required = 'partnership.delete_uclmanagemententity'

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/ucl_management_entities/includes/uclmanagemententity_delete_form.html'
        return self.template_name
