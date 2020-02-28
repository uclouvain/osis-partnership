from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from partnership.forms import MediaForm, PartnershipAgreementForm
from partnership.models import Partnership


class PartnershipAgreementsMixin(LoginRequiredMixin, UserPassesTestMixin):
    context_object_name = 'agreement'
    login_url = 'access_denied'

    def dispatch(self, request, *args, **kwargs):
        self.partnership = get_object_or_404(Partnership, pk=kwargs['partnership_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.partnership.agreements.all()

    def get_success_url(self):
        return self.partnership.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['partnership'] = self.partnership
        return context


class PartnershipAgreementsFormMixin(PartnershipAgreementsMixin):
    form_class = PartnershipAgreementForm
    login_url = 'access_denied'

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/includes/partnership_agreement_form.html'
        return self.template_name

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_form_media(self):
        kwargs = self.get_form_kwargs()
        kwargs['prefix'] = 'media'
        if self.object is not None:
            kwargs['instance'] = self.object.media
        del kwargs['user']
        form = MediaForm(**kwargs)
        del form.fields['type']
        return form

    def get_context_data(self, **kwargs):
        if 'form_media' not in kwargs:
            kwargs['form_media'] = self.get_form_media()
        return super().get_context_data(**kwargs)

    def check_dates(self, agreement):
        if agreement.start_academic_year.year < self.partnership.start_academic_year.year:
            messages.warning(self.request, _('partnership_agreement_warning_before'))
        if agreement.end_academic_year.year > self.partnership.end_academic_year.year:
            messages.warning(self.request, _('partnership_agreement_warning_after'))

    def get_filename(self, filename):
        extension = filename.split('.')[-1]
        return 'partnership_agreement_{}_{}.{}'.format(
            self.partnership.pk,
            self.partnership.partner.pk,
            extension,
        )

    def form_invalid(self, form, form_media):
        messages.error(self.request, _('partnership_agreement_error'))
        return self.render_to_response(self.get_context_data(form=form, form_media=form_media))

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        form_media = self.get_form_media()
        # Do the valid before to ensure the errors are calculated
        form_media_valid = form_media.is_valid()
        if form.is_valid() and form_media_valid:
            return self.form_valid(form, form_media)
        else:
            return self.form_invalid(form, form_media)
