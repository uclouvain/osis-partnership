from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_cte import CTEQuerySet
from rules import RuleSet

from osis_role.contrib.models import EntityRoleModel, EntityRoleModelQueryset
from partnership.auth.predicates import *
from partnership.models import PartnershipType


class PartnershipEntityManagerQuerySet(CTEQuerySet, EntityRoleModelQueryset):
    pass


class PartnershipEntityManager(EntityRoleModel):
    """
    Remplace PersonEntity et ManagementEntity dans le cadre de partnership.

    Utilisé à l'origine pour séparer les permissions des partenariats du reste d'OSIS.
    """
    scopes = ArrayField(
        models.CharField(max_length=200, choices=PartnershipType.choices()),
        blank=True,
    )

    objects = PartnershipEntityManagerQuerySet.as_manager()

    class Meta:
        verbose_name = _("Partnership manager")
        verbose_name_plural = _("Partnership managers")
        group_name = "partnership_managers"

    @classmethod
    def rule_set(cls):
        can_change_agreement = (
                is_linked_to_adri_entity
                | (is_agreement_waiting & is_faculty_manager_for_agreement)
        )
        return RuleSet({
            # Partnership
            'partnership.add_partnership':
                (is_linked_to_adri_entity | is_faculty_manager)
                & partnership_type_allowed_for_user_scope,
            'partnership.change_partnership':
                (is_linked_to_adri_entity | is_faculty_manager_for_partnership)
                & partnership_allowed_for_user_scope,

            # PartnershipAgreement
            'partnership.change_agreement': can_change_agreement,
            'partnership.delete_agreement':
                ~is_agreement_validated & can_change_agreement,

            # UCLManagementEntity
            'partnership.view_uclmanagemententity':
                is_linked_to_adri_entity | is_faculty_manager,
            'partnership.add_uclmanagemententity':
                is_linked_to_adri_entity,
            'partnership.change_uclmanagemententity':
                is_linked_to_adri_entity | is_faculty_manager_for_ume,
            'partnership.delete_uclmanagemententity':
                is_linked_to_adri_entity & ~ume_has_partnerships,

            # Financing
            'partnership.import_financing': is_linked_to_adri_entity,
            'partnership.export_financing': is_linked_to_adri_entity,

            # Partner
            'partnership.add_partner':
                is_linked_to_adri_entity | is_faculty_manager,
            'partnership.change_partner': is_linked_to_adri_entity,

            # PartnerEntity
            'partnership.add_partnerentity':
                is_linked_to_adri_entity | is_faculty_manager,
            'partnership.change_partnerentity':
                is_linked_to_adri_entity | is_in_same_faculty_as_author,
            'partnership.delete_partnerentity':
                (is_linked_to_adri_entity | is_in_same_faculty_as_author)
                & ~entity_has_partnerships
                & ~entity_has_children,
        })
