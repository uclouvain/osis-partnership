from django.views.generic import DeleteView

from .mixins import PartnerEntityMixin

__all__ = [
    'PartnerEntityDeleteView',
]


class PartnerEntityDeleteView(PartnerEntityMixin, DeleteView):
    template_name = 'partnerships/partners/entities/partner_entity_delete.html'
    context_object_name = 'partner_entity'
    permission_required = 'partnership.delete_partnerentity'

    def get_template_names(self):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return 'partnerships/partners/entities/includes/partner_entity_delete.html'
        return self.template_name
