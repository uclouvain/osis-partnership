from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import UpdateView

from base.models.academic_year import find_academic_years
from partnership.auth.predicates import is_linked_to_adri_entity
from partnership.models import (
    PartnershipType, PartnershipYear, PartnershipPartnerRelation,
)
from partnership.models.relation_year import PartnershipPartnerRelationYear
from partnership.views.mixins import NotifyAdminMailMixin
from partnership.views.partnership.mixins import PartnershipFormMixin

__all__ = [
    'PartnershipUpdateView',
]


class PartnershipUpdateView(PartnershipFormMixin,
                            NotifyAdminMailMixin,
                            UpdateView):
    template_name = "partnerships/partnership/partnership_update.html"
    permission_required = 'partnership.change_partnership'

    def dispatch(self, *args, **kwargs):
        self.object = self.get_object()
        self.partnership_type = self.object.partnership_type
        return super().dispatch(*args, **kwargs)

    @transaction.atomic
    def form_valid(self, form, form_year):
        partnership = form.save()

        year_data = form_year.cleaned_data
        new_end_year = year_data.get('end_academic_year')
        if (new_end_year and new_end_year != self.object.end_academic_year
                and not is_linked_to_adri_entity(self.request.user)):
            title = _('partnership_end_year_updated_{partner}_{faculty}').format(
                partner=partnership.first_partner_name,
                faculty=partnership.ucl_entity.most_recent_acronym,
            )
            self.notify_admin_mail(title, 'partnership_update.html', {
                'partnership': partnership,
            })

        start_year = None
        start_academic_year = year_data.get('start_academic_year', None)
        # Create missing start year if needed
        if start_academic_year is not None:
            start_year = start_academic_year.year
            first_year = partnership.years.order_by(
                'academic_year__year'
            ).select_related('academic_year').first()
            if first_year is not None:
                first_year_education_fields = first_year.education_fields.all()
                first_year_education_levels = first_year.education_levels.all()
                first_year_entities = first_year.entities.all()
                first_year_offers = first_year.offers.all()
                academic_years = find_academic_years(
                    start_year=start_year,
                    end_year=first_year.academic_year.year - 1
                )
                for academic_year in academic_years:
                    first_year.id = None
                    first_year.academic_year = academic_year
                    first_year.save()
                    first_year.education_fields.set(first_year_education_fields)
                    first_year.education_levels.set(first_year_education_levels)
                    first_year.entities.set(first_year_entities)
                    first_year.offers.set(first_year_offers)

        # Update years
        if partnership.partnership_type in PartnershipType.with_synced_dates():
            from_year = year_data['from_academic_year'].year
            end_year = year_data['end_academic_year'].year

            academic_years = find_academic_years(
                start_year=from_year,
                end_year=end_year,
            )
        else:
            academic_years = find_academic_years(
                # We need academic years surrounding this time range
                start_date=partnership.end_date,
                end_date=partnership.start_date,
            )
            end_year = academic_years.last().year



        for academic_year in academic_years:
            partnership_year = form_year.save(commit=False)
            existing_year = PartnershipYear.objects.filter(
                partnership=partnership, academic_year=academic_year
            ).first()

            partnership_year.pk = existing_year.pk if existing_year else None
            partnership_year.partnership = partnership
            partnership_year.academic_year = academic_year
            partnership_year.save()
            form_year.save_m2m()

        # Delete no longer used years
        if partnership.partnership_type in PartnershipType.with_synced_dates():
            query = Q(academic_year__year__gt=end_year)
            if start_academic_year is not None:
                query |= Q(academic_year__year__lt=start_year)
        else:
            query = Q(academic_year__start_date__gt=partnership.end_date)
            query |= Q(academic_year__end_date__lt=partnership.start_date)
        partnership.years.filter(query).delete()

        # code added when business request to add co-diplomation (program FIE and osis base history)
        if self.partnership_type == "COURSE":
            entities = PartnershipPartnerRelation.objects.filter(partnership=partnership)
            for entity in entities:
                for academic_year in academic_years:
                    # update or create according to range start_year and end_year
                    object, created = PartnershipPartnerRelationYear.objects.get_or_create(
                        partnership_relation_id=entity.pk,
                        academic_year=academic_year
                    )
            # delete according to range start_year and end_year
            object = PartnershipPartnerRelationYear.objects.filter(
                partnership_relation_id__in=entities).filter(
                Q(academic_year__year__gt=end_year) | Q(academic_year__year__lt=start_year)
            ).delete()


        # Sync dates
        if not form.cleaned_data.get('start_date') and start_academic_year:
            partnership.start_date = start_academic_year.start_date
            partnership.save()
        if not form.cleaned_data.get('end_date'):
            partnership.end_date = year_data['end_academic_year'].end_date
            partnership.save()

        messages.success(self.request, _('partnership_success'))
        if self.partnership_type == "COURSE":
            return redirect(reverse_lazy('partnerships:complement', kwargs={'pk': partnership.pk}))
        return redirect(partnership)
