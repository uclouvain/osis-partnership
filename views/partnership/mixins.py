from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from base.models.academic_year import current_academic_year
from osis_role.contrib.views import PermissionRequiredMixin
from partnership.forms import (
    PartnershipForm, PartnershipYearForm
)
from partnership.models import (
    Partnership, PartnershipConfiguration
)

__all__ = [
    'PartnershipRelatedMixin',
    'PartnershipFormMixin',
]


class PartnershipRelatedMixin(PermissionRequiredMixin):
    login_url = 'access_denied'
    permission_required = 'partnership.change_partnership'

    def dispatch(self, request, *args, **kwargs):
        self.partnership = get_object_or_404(Partnership, pk=kwargs['partnership_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_permission_object(self):
        return self.partnership

    def get_success_url(self):
        return self.partnership.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['partnership'] = self.partnership
        return context


class PartnershipFormMixin:
    model = Partnership
    form_class = PartnershipForm
    login_url = 'access_denied'

    def get_form_year(self):
        kwargs = self.get_form_kwargs()
        kwargs['prefix'] = 'year'
        partnership = kwargs['instance']
        if partnership is not None:
            configuration = PartnershipConfiguration.get_configuration()
            current_academic_year = configuration.get_current_academic_year_for_creation_modification()
            kwargs['instance'] = partnership.years.filter(academic_year=current_academic_year).first()
            if kwargs['instance'] is None:
                # No current year for this partnership, get the last available
                kwargs['instance'] = partnership.years.last()
        return PartnershipYearForm(**kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user

        partnership_type = self.kwargs.get('type')
        kwargs['partnership_type'] = (
            partnership_type.name if partnership_type
            else kwargs['instance'].partnership_type
        )
        return kwargs

    def get_context_data(self, **kwargs):
        if 'form_year' not in kwargs:
            kwargs['form_year'] = self.get_form_year()
        kwargs['current_academic_year'] = current_academic_year()
        kwargs['form_template'] = "partnerships/includes/partnership_form_{}.html".format(
            self.get_form_kwargs().get('partnership_type')
        )

        return super().get_context_data(**kwargs)

    def form_invalid(self, form, form_year):
        messages.error(self.request, _('partnership_error'))
        return self.render_to_response(self.get_context_data(form=form, form_year=form_year))

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        form_year = self.get_form_year()
        form_year_is_valid = form_year.is_valid()
        if form.is_valid() and form_year_is_valid:
            return self.form_valid(form, form_year)
        else:
            return self.form_invalid(form, form_year)
