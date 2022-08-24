from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, TemplateView

from base.models.academic_year import find_academic_years
from partnership.auth.predicates import is_linked_to_adri_entity
from partnership.models import Partnership, PartnershipType
from partnership.views.mixins import NotifyAdminMailMixin
from partnership.views.partnership.mixins import PartnershipFormMixin

__all__ = [
    'PartnershipCreateView',
    'PartnershipTypeChooseView',
]


class PartnershipTypeChooseView(LoginRequiredMixin, UserPassesTestMixin,
                                TemplateView):
    template_name = 'partnerships/partnership/type_choose.html'
    login_url = 'access_denied'

    def test_func(self):
        return bool(self.extra_context['types'])

    def dispatch(self, request, *args, **kwargs):
        # Get all types the user can create
        types = [t for t in PartnershipType
                 if request.user.has_perm('partnership.add_partnership', t)]
        self.extra_context = {'types': types}
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # Redirect if there is only one type
        types = self.extra_context['types']
        if len(types) == 1:
            return redirect('partnerships:create', type=types[0])

        # Display template
        return super().get(request, *args, **kwargs)


class PartnershipCreateView(NotifyAdminMailMixin,
                            PartnershipFormMixin,
                            CreateView):
    model = Partnership
    template_name = "partnerships/partnership/partnership_create.html"
    login_url = 'access_denied'
    permission_required = 'partnership.add_partnership'

    def get_permission_object(self):
        self.partnership_type = self.kwargs['type'].name
        return self.kwargs['type']

    @transaction.atomic
    def form_valid(self, form, form_year):
        partnership = form.save(commit=False)
        partnership.author = self.request.user.person

        if partnership.partnership_type in PartnershipType.with_synced_dates():
            start_academic_year = form_year.cleaned_data['start_academic_year']
            end_academic_year = form_year.cleaned_data['end_academic_year']
            partnership.start_date = start_academic_year.start_date
            partnership.end_date = end_academic_year.end_date
        else:
            years = find_academic_years(
                # We need academic years surrounding this time range
                start_date=partnership.end_date,
                end_date=partnership.start_date,
            )
            start_academic_year = years.first()
            end_academic_year = years.last()

        # Resume saving
        partnership.save()
        form.save_m2m()

        # Create years
        start_year = start_academic_year.year
        end_year = end_academic_year.year
        academic_years = find_academic_years(start_year=start_year, end_year=end_year)
        for academic_year in academic_years:
            partnership_year = form_year.save(commit=False)
            partnership_year.id = None  # Force the creation of a new PartnershipYear
            partnership_year.partnership = partnership
            partnership_year.academic_year = academic_year
            partnership_year.save()
            form_year.save_m2m()

        messages.success(self.request, _('partnership_success'))
        if not is_linked_to_adri_entity(self.request.user):
            title = '{} - {}'.format(
                _('partnership_created'),
                partnership.ucl_entity.most_recent_acronym
            )
            self.notify_admin_mail(title, 'partnership_creation.html', {
                'partnership': Partnership.objects.get(pk=partnership.pk),  # Reload to get annotations
            })
        return redirect(partnership)

    def post(self, request, *args, **kwargs):
        self.object = None
        return super().post(request, *args, **kwargs)
