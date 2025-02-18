from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import CreateView, TemplateView, UpdateView, FormView
from base.models.academic_year import find_academic_years, AcademicYear
from partnership.auth.predicates import is_linked_to_adri_entity
from partnership.forms.partnership.partnership import PartnershipPartnerRelationFormSet
from partnership.forms.partnership.year import PartnerRelationYearFormSet, PartnershipRelationYearWithoutDatesForm
from partnership.models import Partnership, PartnershipType, PartnershipPartnerRelation, PartnershipConfiguration
from partnership.models.relation_year import PartnershipPartnerRelationYear
from partnership.views.mixins import NotifyAdminMailMixin
from osis_role.contrib.views import PermissionRequiredMixin

__all__ = [
    'PartnershipCreateView',
    'PartnershipTypeChooseView',
]

from partnership.views.partnership.mixins import PartnershipFormMixin, PartnershipRelatedMixin


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

        # create partnershiprelationyear
        if self.partnership_type == "COURSE":
            entities = PartnershipPartnerRelation.objects.filter(partnership=partnership)
            for entity in entities:
                for academic_year in academic_years:
                    PartnershipPartnerRelationYear.objects.create(
                        partnership_relation_id=entity.pk,
                        academic_year=academic_year
                    )

        messages.success(self.request, _('partnership_success'))
        if not is_linked_to_adri_entity(self.request.user):
            title = '{} - {}'.format(
                _('partnership_created'),
                partnership.ucl_entity.most_recent_acronym
            )
            self.notify_admin_mail(title, 'partnership_creation.html', {
                'partnership': Partnership.objects.get(pk=partnership.pk),  # Reload to get annotations
            })

        if self.partnership_type == "COURSE":
            return redirect(reverse_lazy('partnerships:complement', kwargs={'pk': partnership.pk}))
        return redirect(partnership)

    def post(self, request, *args, **kwargs):
        self.object = None
        return super().post(request, *args, **kwargs)



class PartnershipPartnerRelationUpdateView(FormView):
    model = Partnership
    template_name = 'partnerships/partnership/partnership_relation_update.html'
    success_url = 'partnerships:detail'
    login_url = 'access_denied'
    permission_required = 'partnership.change_partnership'
    form_class = PartnershipRelationYearWithoutDatesForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        self.partnership = get_object_or_404(Partnership, pk=self.kwargs['pk'])
        kwargs['user'] = self.request.user
        kwargs['instance'] = self.partnership
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['partnership'] = self.partnership

        config = PartnershipConfiguration.get_configuration()
        current_academic_year = config.partnership_creation_update_min_year
        start_year = self.partnership.start_date

        if start_year.year > current_academic_year.year:
            queryset = PartnershipPartnerRelationYear.objects.filter(
                partnership_relation__partnership=self.partnership,
                academic_year__year = start_year.year
            ).select_related(
                'partnership_relation__entity__organization')
        else:
            queryset = PartnershipPartnerRelationYear.objects.filter(
                        partnership_relation__partnership=self.partnership,
                        academic_year__year = current_academic_year
                    ).select_related(
                        'partnership_relation__entity__organization')

        context['formset'] = PartnerRelationYearFormSet(
            queryset=queryset
        )

        return context

    def post(self, request, *args, **kwargs):
        self.partnership = get_object_or_404(Partnership, pk=self.kwargs['pk'])
        form = self.get_form()
        formset = PartnerRelationYearFormSet(request.POST)

        if "start_academic_year" in form.errors:
            messages.error(self.request, _('partnership_error'))
            return self.render_to_response(self.get_context_data(form=form, formset=formset))
        elif "from_academic_year" in form.errors:
            messages.error(self.request, _('partnership_error'))
            return self.render_to_response(self.get_context_data(form=form, formset=formset))
        elif "end_academic_year" in form.errors:
            messages.error(self.request, _('partnership_error'))
            return self.render_to_response(self.get_context_data(form=form, formset=formset))

        if formset.is_valid():
            modification_academic_year = form.cleaned_data.get('from_academic_year')

            if modification_academic_year:
                current_academic_year_id = modification_academic_year.pk
                end_year = self.partnership.end_date.year
                academic_years = find_academic_years(start_year=modification_academic_year.year, end_year=end_year)

                instances = formset.save(commit=False)
                count = 0
                for instance in instances:
                    relation = instance.partnership_relation
                    for year in academic_years:
                        obj = PartnershipPartnerRelationYear.objects.filter(
                            partnership_relation=relation,
                            academic_year=year.id)
                        result = obj.update(
                            type_diploma_by_partner=instance.type_diploma_by_partner,
                            diploma_prod_by_partner=instance.diploma_prod_by_partner,
                            supplement_prod_by_partner=instance.supplement_prod_by_partner,
                            partner_referent=instance.partner_referent,
                        )
                        count = count + result
                if count > 0:
                    mess = f'Mise à jour avec succès de {count} instance'
                    messages.success(self.request, mess)
                else :
                    mess = f"Aucune instance n'a été mise à jour"
                    messages.error(self.request, mess)

            return redirect(reverse_lazy(self.success_url, kwargs={'pk': self.partnership.id}))
        else:
            messages.error(self.request, _('partnership_error'))
        return self.render_to_response(self.get_context_data(form=form, formset=formset))

