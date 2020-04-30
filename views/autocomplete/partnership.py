from datetime import date

from dal import autocomplete
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Exists, OuterRef, Q, Subquery

from base.models.education_group_year import EducationGroupYear
from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.enums.entity_type import FACULTY
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


def get_faculty_id(entity_id):
    """
    Returns the faculty id of an entity (which can be a faculty or a labo)
    :param entity_id:
    :return: faculty_id
    """
    faculty = entity_id
    entity_version = EntityVersion.objects.filter(
        entity=entity_id
    ).order_by('-start_date').first()
    if entity_version and entity_version.entity_type != FACULTY:
        faculty = entity_version.parent_id
    return faculty


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
    """
    Autocomplete for entities on PartnershipYearForm
    """
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        """
        Return the children when entity is a faculty,
        or the siblings when entity is a labo
        """
        # entity is the hidden field of PartnershipYearForm
        entity_id = self.forwarded.get('entity', None)
        if entity_id is None:
            return Entity.objects.none()

        # Get faculty (entity if faculty, or parent if not faculty)
        faculty = get_faculty_id(entity_id)

        latest = EntityVersion.objects.filter(
            entity=OuterRef('pk')
        ).order_by('-start_date')

        # Get all valid children of faculty
        cte = EntityVersion.objects.with_parents(entity=faculty)
        qs = Entity.objects.filter(pk__in=Subquery(
            cte.queryset().with_cte(cte).values('entity_id')
        )).exclude(pk=faculty).annotate(
            most_recent_acronym=Subquery(latest.values('acronym')[:1]),
            title=Subquery(latest.values('title')[:1]),
        ).annotate(
            is_valid=Exists(latest.exclude(end_date__lte=date.today()))
        ).filter(is_valid=True).order_by('most_recent_acronym')

        if self.q:
            qs = qs.filter(most_recent_acronym__icontains=self.q)
        return qs.distinct()

    def get_result_label(self, result):
        return '{0.most_recent_acronym} - {0.title}'.format(result)


class PartnershipYearOffersAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    """
    Autocomplete for offers on partnership create/update form
    """
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        config = PartnershipConfiguration.get_configuration()
        next_academic_year = config.partnership_creation_update_min_year

        education_levels = self.forwarded.get('education_levels', None)
        entities = self.forwarded.get('entities', None)
        entity = self.forwarded.get('entity', None)

        # Return nothing if we don't have all the data
        if education_levels is None or (entities is None and entity is None):
            return EducationGroupYear.objects.none()

        qs = EducationGroupYear.objects.filter(
            joint_diploma=True,
            # academic_year=next_academic_year,
            education_group_type__partnership_education_levels__in=education_levels,
        ).select_related('academic_year')

        # Entities filter
        if entities is not None:
            qs = qs.filter(
                Q(management_entity__in=entities)
                | Q(administration_entity__in=entities)
            )
        else:
            # entity is the hidden field of PartnershipYearForm, updated by JS
            faculty = get_faculty_id(entity)

            qs = qs.filter(
                Q(management_entity=faculty)
                | Q(administration_entity=faculty)
                | Q(management_entity__entityversion__parent=faculty)
                | Q(administration_entity__entityversion__parent=faculty)
            )

        # Query filter
        if self.q:
            qs = qs.filter(title__icontains=self.q)
        return qs.distinct('education_group').order_by('education_group')

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
    """
    Autocomplete for entities on partnership list filter form
    """
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = super().get_queryset()
        ucl_entity = self.forwarded.get('ucl_entity', None)
        if ucl_entity:
            qs = qs.filter(entityversion__parent=ucl_entity)
        else:
            return qs.none()
        qs = qs.filter(partnerships_years__isnull=False)
        return qs
