from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import ListView

from partnership.models import Partnership
from partnership.utils import user_is_adri

from .mixins import PartnershipListFilterMixin

__all__ = [
    'PartnershipsListView',
]


class PartnershipsListView(PermissionRequiredMixin, PartnershipListFilterMixin, ListView):
    template_name = 'partnerships/partnership/partnership_list.html'
    context_object_name = 'partnerships'
    paginate_by = 20
    paginate_orphans = 2
    paginate_neighbours = 4
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_template_names(self):
        if self.is_agreements:
            if self.request.is_ajax():
                return 'partnerships/agreements/includes/agreements_list_results.html'
            else:
                return 'partnerships/partnership/partnership_list.html'
        else:
            if self.request.is_ajax():
                return 'partnerships/includes/partnerships_list_results.html'
            else:
                return 'partnerships/partnership/partnership_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['paginate_neighbours'] = self.paginate_neighbours
        context['can_change_configuration'] = user_is_adri(self.request.user)
        context['can_add_partnership'] = Partnership.user_can_add(self.request.user)
        return context
