from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _
from rules import RuleSet

from osis_role.contrib.models import EntityRoleModel, EntityRoleModelQueryset
from partnership.auth.predicates import *
from partnership.models import PartnershipType


class PartnershipEntityManager(EntityRoleModel):
    """
    Remplace PersonEntity et ManagementEntity dans le cadre de partnership.

    Utilisé à l'origine pour séparer les permissions des partenariats du reste d'OSIS.
    """
    scopes = ArrayField(
        models.CharField(max_length=200, choices=PartnershipType.choices()),
        blank=True,
    )

    objects = EntityRoleModelQueryset.as_manager()

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
            'partnership.can_access_partnerships': rules.always_allow,
            'partnership.add_partnership':
                (is_linked_to_adri_entity | is_faculty_manager)
                & partnership_type_allowed_for_user_scope,
            'partnership.change_partnership':
                (is_linked_to_adri_entity | is_faculty_manager_for_partnership)
                & partnership_allowed_for_user_scope,
            'partnership.delete_partnership':
                (is_linked_to_adri_entity & partnership_allowed_for_user_scope
                 & ~partnership_has_agreement),

            # PartnershipAgreement
            'partnership.can_access_partnerships_agreements': rules.always_allow,
            'partnership.change_agreement': can_change_agreement,
            'partnership.delete_agreement':
                ~is_agreement_validated & can_change_agreement,

            # UCLManagementEntity
            'partnership.view_uclmanagemententity':
                (is_linked_to_adri_entity | is_faculty_manager) & (has_mobility_scope | has_course_scope),
            'partnership.add_uclmanagemententity':
                (is_linked_to_adri_entity) & (has_mobility_scope | has_course_scope),
            'partnership.change_uclmanagemententity':
                (is_linked_to_adri_entity | is_faculty_manager_for_ume) & (has_mobility_scope | has_course_scope),
            'partnership.delete_uclmanagemententity':
                (is_linked_to_adri_entity & ~ume_has_partnerships) & has_mobility_scope,

            # Financing
            'partnership.add_funding': is_linked_to_adri_entity,
            'partnership.change_funding': is_linked_to_adri_entity,
            'partnership.delete_funding': is_linked_to_adri_entity,
            'partnership.change_financing': has_mobility_scope,
            'partnership.import_financing': is_linked_to_adri_entity & has_mobility_scope,
            'partnership.export_financing': is_linked_to_adri_entity & has_mobility_scope,

            # Partner
            'partnership.can_access_partners': rules.always_allow,
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

            # Configuration
            'partnership.change_partnershipconfiguration': is_linked_to_adri_entity,
        })
