from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import FormMixin

from partnership import perms
from partnership.forms import ContactForm
from partnership.models import Partnership


class PartnershipContactMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = 'access_denied'

    def test_func(self):
        return perms.user_can_change_partnership(self.request.user, self.partnership)

    def dispatch(self, request, *args, **kwargs):
        self.partnership = get_object_or_404(Partnership, pk=kwargs['partnership_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.partnership.contacts.all()

    def get_success_url(self):
        return self.partnership.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['partnership'] = self.partnership
        return context


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
