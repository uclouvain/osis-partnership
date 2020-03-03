from datetime import date

from dal import autocomplete
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Exists, OuterRef, Q, Subquery

from base.models.education_group_year import EducationGroupYear
from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from partnership.models import (
    Partner, PartnerEntity, Partnership, PartnershipConfiguration,
)

from .faculty import FacultyEntityAutocompleteView

__all__ = [
    'PartnershipAutocompleteView',
    'PartnerAutocompletePartnershipsFilterView',
    'PartnerEntityAutocompletePartnershipsFilterView',
    'PartnershipYearEntitiesAutocompleteView',
    'PartnershipYearOffersAutocompleteView',
    'YearsEntityAutocompleteFilterView',
]


class PartnershipAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = Partnership.objects.all()
        if self.q:
            qs = qs.filter(
                Q(partner__name__icontains=self.q)
                | Q(partner_entity__name__icontains=self.q)
            )
        return qs.distinct()


class PartnershipYearEntitiesAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        faculty = self.forwarded.get('faculty', None)
        if faculty is not None:
            qs = Entity.objects.annotate(
                most_recent_acronym=Subquery(
                    EntityVersion.objects
                        .filter(entity=OuterRef('pk'))
                        .order_by('-start_date')
                        .values('acronym')[:1]
                ),
            ).filter(entityversion__parent=faculty)
        else:
            return Entity.objects.none()
        qs = qs.annotate(
            is_valid=Exists(
                EntityVersion.objects
                .filter(entity=OuterRef('pk'))
                .exclude(end_date__lte=date.today())
            )
        ).filter(is_valid=True)
        if self.q:
            qs = qs.filter(most_recent_acronym__icontains=self.q)
        return qs.distinct()

    def get_result_label(self, result):
        try:
            title = result.entityversion_set.latest("start_date").title
            return '{0.most_recent_acronym} - {1}'.format(result, title)
        except EntityVersion.DoesNotExist:
            return result.most_recent_acronym


class PartnershipYearOffersAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = EducationGroupYear.objects.filter(joint_diploma=True).select_related('academic_year')
        next_academic_year = \
            PartnershipConfiguration.get_configuration().get_current_academic_year_for_creation_modification()
        qs = qs.filter(academic_year=next_academic_year)
        # Education levels filter
        education_levels = self.forwarded.get('education_levels', None)
        if education_levels is not None:
            qs = qs.filter(education_group_type__partnership_education_levels__in=education_levels)
        else:
            return EducationGroupYear.objects.none()
        # Entities filter
        entities = self.forwarded.get('entities', None)
        if entities is not None:
            qs = qs.filter(Q(management_entity__in=entities) | Q(administration_entity__in=entities))
        else:
            faculty = self.forwarded.get('faculty', None)
            if faculty is not None:
                qs = qs.filter(
                    Q(management_entity=faculty) | Q(administration_entity=faculty)
                    | Q(management_entity__entityversion__parent=faculty)
                    | Q(administration_entity__entityversion__parent=faculty)
                )
            else:
                return EducationGroupYear.objects.none()
        # Query filter
        if self.q:
            qs = qs.filter(title__icontains=self.q)
        return qs.distinct('education_group').order_by()

    def get_result_label(self, result):
        return '{0.acronym} - {0.title}'.format(result)


class PartnerAutocompletePartnershipsFilterView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = Partner.objects.filter(partnerships__isnull=False)
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs.distinct()


class PartnerEntityAutocompletePartnershipsFilterView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = PartnerEntity.objects.filter(partnerships__isnull=False)
        partner = self.forwarded.get('partner', None)
        if partner:
            qs = qs.filter(partner=partner)
        else:
            return PartnerEntity.objects.none()
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs.distinct()


class YearsEntityAutocompleteFilterView(FacultyEntityAutocompleteView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(partnerships_years__isnull=False)
        return qs
