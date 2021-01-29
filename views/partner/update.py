from django.core.exceptions import PermissionDenied
from django.views.generic import UpdateView

from base.models.enums.organization_type import MAIN
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

    def dispatch(self, request, *args, **kwargs):
        # Prevent editing MAIN organizations
        if self.get_object().organization.type == MAIN:
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)


class PartnerEntityUpdateView(PartnerEntityFormMixin, UpdateView):
    template_name = 'partnerships/partners/entities/partner_entity_update.html'
    context_object_name = 'partner_entity'
    permission_required = 'partnership.change_partnerentity'
