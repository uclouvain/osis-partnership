from dal import autocomplete
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q

from base.models.education_group_year import EducationGroupYear
from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.enums.entity_type import DOCTORAL_COMMISSION, FACULTY, SECTOR
from partnership.models import (
    Partner,
    PartnerEntity,
    Partnership,
    PartnershipConfiguration,
    PartnershipSubtype,
    PartnershipType,
)
from .faculty import FacultyEntityAutocompleteView

__all__ = [
    'PartnershipAutocompleteView',
    'PartnerAutocompletePartnershipsFilterView',
    'PartnerEntityAutocompletePartnershipsFilterView',
    'PartnershipYearEntitiesAutocompleteView',
    'PartnershipYearOffersAutocompleteView',
    'YearsEntityAutocompleteFilterView',
    'PartnershipSubtypeAutocompleteView',
]


def get_parent_id(entity_id, entity_type):
    """
    Returns the faculty id of an entity (which can be a faculty or a labo)
    :param entity_id: The child id from where to search
    :param entity_type: The type of parent to find
    """
    cte = EntityVersion.objects.with_children(entity=entity_id)
    return cte.join(EntityVersion, id=cte.col.id).with_cte(cte).filter(
        entity_type=entity_type
    ).values_list('entity_id', flat=True).first()


class PartnershipAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = Partnership.objects.all()
        if self.q:
            qs = qs.filter(
                Q(partner__organization__name__icontains=self.q)
                | Q(partner_entity__name__icontains=self.q)
            )
        return qs.distinct()


class PartnershipYearEntitiesAutocompleteView(FacultyEntityAutocompleteView):
    """
    Autocomplete for entities on PartnershipYearForm
    """
    def get_queryset(self):
        """
        Return the children when entity is a faculty,
        or the siblings when entity is a labo
        """
        # entity is the hidden field of PartnershipYearForm
        entity_id = self.forwarded.get('entity', None)
        if entity_id is None:
            return Entity.objects.none()

        partnership_type = self.forwarded.get('partnership_type', None)
        if partnership_type == PartnershipType.DOCTORATE.name:
            # We need the sector
            parent_id = get_parent_id(entity_id, SECTOR)
        else:
            # Get faculty (entity if faculty, or parent if not faculty)
            parent_id = get_parent_id(entity_id, FACULTY)

        cte = EntityVersion.objects.with_parents(entity_id=parent_id)
        cte_qs = cte.queryset().with_cte(cte).values('entity_id')

        qs = super().get_queryset().filter(pk__in=cte_qs).exclude(pk=parent_id)

        if partnership_type == PartnershipType.DOCTORATE.name:
            # Only return doctoral commissions for this type
            qs = qs.filter(entityversion__entity_type=DOCTORAL_COMMISSION)

        return qs


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
            academic_year=next_academic_year,
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
            faculty = get_parent_id(entity, FACULTY)

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
            qs = qs.filter(organization__name__icontains=self.q)
        return qs.distinct()


class PartnerEntityAutocompletePartnershipsFilterView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = PartnerEntity.objects.filter(partnerships__isnull=False)
        partner = self.forwarded.get('partner', None)
        if partner:
            qs = qs.filter(
                entity__entityversion__parent__organization__partner=partner,
            )
        else:
            return PartnerEntity.objects.none()
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs.distinct()


class YearsEntityAutocompleteFilterView(FacultyEntityAutocompleteView):
    """
    Autocomplete for entities on partnership list filter form
    """
    def get_queryset(self):
        entity = self.forwarded.get('ucl_entity', None)
        if entity is None:
            return Entity.objects.none()

        # Get all children of faculty
        faculty = get_parent_id(entity, FACULTY)
        cte = EntityVersion.objects.with_parents(entity=faculty)
        qs = cte.queryset().with_cte(cte).values('entity_id')

        # Must have partnership_years associated
        return super().get_queryset().filter(
            partnerships_years__isnull=False,
            pk__in=qs,
        )


class PartnershipSubtypeAutocompleteView(PermissionRequiredMixin,
                                         autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'
    model = PartnershipSubtype

    def get_queryset(self):
        queryset = super().get_queryset()
        partnership_type = self.forwarded.get('partnership_type', None)
        if not partnership_type:
            return queryset.none()

        return queryset.filter(types__contains=[partnership_type])
