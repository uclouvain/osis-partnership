from django.views.generic import UpdateView

from partnership.models import Partner
from .mixins import PartnerEntityFormMixin, PartnerFormMixin

__all__ = [
    'PartnerUpdateView',
    'PartnerEntityUpdateView',
]


class PartnerUpdateView(PartnerFormMixin, UpdateView):
    template_name = 'partnerships/partners/partner_update.html'
    prefix = 'partner'
    model = Partner
    permission_required = 'partnership.change_partner'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)


class PartnerEntityUpdateView(PartnerEntityFormMixin, UpdateView):
    template_name = 'partnerships/partners/entities/partner_entity_update.html'
    context_object_name = 'partner_entity'
    permission_required = 'partnership.change_partnerentity'
