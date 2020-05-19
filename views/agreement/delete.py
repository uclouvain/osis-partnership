from django.views.generic import DeleteView

from .mixins import PartnershipAgreementsMixin

__all__ = ['PartnershipAgreementDeleteView']


class PartnershipAgreementDeleteView(PartnershipAgreementsMixin, DeleteView):
    template_name = 'partnerships/agreements/delete.html'
    permission_required = 'partnership.delete_agreement'

    def get_permission_object(self):
        return self.get_object()

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/agreements/includes/delete.html'
        return self.template_name
