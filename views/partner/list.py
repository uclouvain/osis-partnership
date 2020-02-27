from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import ListView

from partnership import perms
from .mixins import PartnersListFilterMixin

__all__ = [
    'PartnersListView',
]


class PartnersListView(PermissionRequiredMixin, PartnersListFilterMixin, ListView):
    context_object_name = 'partners'
    paginate_by = 20
    paginate_orphans = 2
    paginate_neighbours = 4
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/partners/includes/partners_list_results.html'
        else:
            return 'partnerships/partners/partners_list.html'

    def get_context_data(self, **kwargs):
        context = super(PartnersListView, self).get_context_data(**kwargs)
        context['paginate_neighbours'] = self.paginate_neighbours
        context['can_add_partner'] = perms.user_can_add_partner(self.request.user)
        return context
