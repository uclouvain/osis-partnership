import rules
from django.utils.translation import gettext_lazy as _
from django_cte import CTEManager

from osis_role.contrib.models import EntityRoleModel
from partnership.auth.predicates import (
    has_children, has_partnerships, is_linked_to_adri_entity, is_faculty_manager,
    is_in_same_faculty_as_author, is_mobility, is_validated, is_agreement_waiting,
    manage_type,
)


class PartnershipEntityManager(EntityRoleModel):
    """
    Remplace PersonEntity et ManagementEntity dans le cadre de partnership.

    Utilisé à l'origine pour séparer les permissions des partenariats du reste d'OSIS.
    """
    objects = CTEManager()

    class Meta:
        verbose_name = _("Partnership manager")
        verbose_name_plural = _("Partnership managers")
        group_name = "partnership_managers"

    @classmethod
    def rule_set(cls):
        can_change_agreement = is_linked_to_adri_entity | (is_agreement_waiting & is_faculty_manager)
        return rules.RuleSet({
            # Partnership
            'partnership.add_partnership': (
                    (is_mobility & (is_linked_to_adri_entity | is_faculty_manager))
                    | manage_type
            ),
            'partnership.change_partnership': (
                    (is_mobility & (is_linked_to_adri_entity | is_faculty_manager))
                    | manage_type
            ),

            # PartnershipAgreement
            'partnership.change_agreement': can_change_agreement,
            'partnership.delete_agreement': ~is_validated & can_change_agreement,

            # UCLManagementEntity
            'partnership.view_uclmanagemententity': is_linked_to_adri_entity | is_faculty_manager,
            'partnership.list_uclmanagemententity': is_linked_to_adri_entity | is_faculty_manager,
            'partnership.add_uclmanagemententity': is_linked_to_adri_entity,
            'partnership.change_uclmanagemententity': is_linked_to_adri_entity | is_faculty_manager,
            'partnership.delete_uclmanagemententity': is_linked_to_adri_entity & ~has_partnerships,

            # Financing
            'partnership.import_financing': is_linked_to_adri_entity,
            'partnership.export_financing': is_linked_to_adri_entity,

            # Partner
            'partnership.add_partner': is_linked_to_adri_entity | is_faculty_manager,
            'partnership.change_partner': is_linked_to_adri_entity,

            # PartnerEntity
            'partnership.add_partnerentity': is_linked_to_adri_entity | is_faculty_manager,
            'partnership.change_partnerentity': is_linked_to_adri_entity | is_in_same_faculty_as_author,
            'partnership.delete_partnerentity': (
                    (is_linked_to_adri_entity | is_in_same_faculty_as_author)
                    & ~has_partnerships
                    & ~has_children
            ),
        })
