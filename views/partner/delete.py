from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import DeleteView

from .mixins import PartnerEntityMixin

__all__ = [
    'PartnerEntityDeleteView',
]


class PartnerEntityDeleteView(LoginRequiredMixin, PartnerEntityMixin, UserPassesTestMixin, DeleteView):
    template_name = 'partnerships/partners/entities/partner_entity_delete.html'
    context_object_name = 'partner_entity'
    login_url = 'access_denied'

    def test_func(self):
        return self.get_object().user_can_delete(self.request.user)

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/partners/entities/includes/partner_entity_delete.html'
        return self.template_name
