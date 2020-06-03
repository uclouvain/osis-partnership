from django.views.generic import CreateView

from .mixins import PartnerEntityFormMixin, PartnerFormMixin

__all__ = [
    'PartnerCreateView',
    'PartnerEntityCreateView',
]


class PartnerCreateView(PartnerFormMixin, CreateView):
    template_name = 'partnerships/partners/partner_create.html'
    initial = {
        'is_valid': True,
    }
    permission_required = 'partnership.add_partner'

    def post(self, request, *args, **kwargs):
        self.object = None
        return super().post(request, *args, **kwargs)


class PartnerEntityCreateView(PartnerEntityFormMixin, CreateView):
    template_name = 'partnerships/partners/entities/partner_entity_create.html'
    permission_required = 'partnership.add_partnerentity'
