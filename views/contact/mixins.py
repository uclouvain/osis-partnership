from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import FormMixin

from partnership.forms import ContactForm
from partnership.views.partnership.mixins import PartnershipRelatedMixin


class PartnershipContactMixin(PartnershipRelatedMixin):
    def get_queryset(self):
        return self.partnership.contacts.all()


class PartnershipContactFormMixin(PartnershipContactMixin, FormMixin):
    login_url = 'access_denied'
    form_class = ContactForm

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/contacts/includes/partnership_contact_form.html'
        return self.template_name

    def form_invalid(self, form):
        messages.error(self.request, _('partner_error'))
        return self.render_to_response(self.get_context_data(
            form=form,
        ))
