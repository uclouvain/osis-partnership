from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.generic import DeleteView

from .mixins import PartnershipContactMixin

__all__ = ['PartnershipContactDeleteView']


class PartnershipContactDeleteView(PartnershipContactMixin, DeleteView):
    template_name = 'partnerships/contacts/contact_confirm_delete.html'
    login_url = 'access_denied'

    def get_template_names(self):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return 'partnerships/contacts/includes/contact_delete_form.html'
        return self.template_name

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _("contact_delete_success"))
        return response
