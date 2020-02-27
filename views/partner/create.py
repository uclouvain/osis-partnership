from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView

from partnership import perms
from partnership.forms import PartnerForm
from .mixins import PartnerEntityFormMixin, PartnerFormMixin

__all__ = [
    'PartnerCreateView',
    'PartnerEntityCreateView',
]


class PartnerCreateView(LoginRequiredMixin, UserPassesTestMixin, PartnerFormMixin, CreateView):
    form_class = PartnerForm
    template_name = 'partnerships/partners/partner_create.html'
    prefix = 'partner'
    initial = {
        'is_valid': True,
    }
    login_url = 'access_denied'

    def test_func(self):
        return perms.user_can_add_partner(self.request.user)

    def post(self, request, *args, **kwargs):
        self.object = None
        return super().post(request, *args, **kwargs)


class PartnerEntityCreateView(LoginRequiredMixin, PartnerEntityFormMixin, UserPassesTestMixin, CreateView):
    template_name = 'partnerships/partners/entities/partner_entity_create.html'
    login_url = 'access_denied'

    def test_func(self):
        return perms.user_can_add_partner(self.request.user)
