from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import UpdateView

from partnership.forms import PartnerForm
from partnership.models import Partner

from .mixins import PartnerEntityFormMixin, PartnerFormMixin

__all__ = [
    'PartnerUpdateView',
    'PartnerEntityUpdateView',
]


class PartnerUpdateView(LoginRequiredMixin, UserPassesTestMixin, PartnerFormMixin, UpdateView):
    form_class = PartnerForm
    template_name = 'partnerships/partners/partner_update.html'
    prefix = 'partner'
    queryset = Partner.objects.select_related('contact_address')
    context_object_name = 'partner'
    login_url = 'access_denied'

    def test_func(self):
        self.object = self.get_object()
        return self.object.user_can_change(self.request.user)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(PartnerUpdateView, self).post(request, *args, **kwargs)


class PartnerEntityUpdateView(LoginRequiredMixin, PartnerEntityFormMixin, UserPassesTestMixin, UpdateView):
    template_name = 'partnerships/partners/entities/partner_entity_update.html'
    context_object_name = 'partner_entity'
    login_url = 'access_denied'

    def test_func(self):
        return self.get_object().user_can_change(self.request.user)
