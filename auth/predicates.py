from datetime import date

import rules
from django.db.models import Q

from partnership.models import PartnershipType


@rules.predicate
def is_agreement_validated(user, agreement):
    from partnership.models import AgreementStatus
    return agreement.status == AgreementStatus.VALIDATED.name


@rules.predicate
def is_agreement_waiting(user, agreement):
    from partnership.models import AgreementStatus
    return agreement.status == AgreementStatus.WAITING.name


@rules.predicate(bind=True)
def is_linked_to_adri_entity(self, user):
    from .roles.partnership_manager import PartnershipEntityManager
    if self.context:
        qs = self.context['role_qs']
    else:
        qs = PartnershipEntityManager.objects.filter(
            person=getattr(user, 'person', None)
        )
    return qs.filter(
        Q(entity__entityversion__end_date__gte=date.today())
        | Q(entity__entityversion__end_date__isnull=True),
        entity__entityversion__start_date__lte=date.today(),
        entity__entityversion__acronym='ADRI',
    ).exists()


@rules.predicate(bind=True)
def is_faculty_manager(self, user):
    from .roles.partnership_manager import PartnershipEntityManager
    if self.context:
        qs = self.context['role_qs']
    else:
        qs = PartnershipEntityManager.objects.filter(
            person=getattr(user, 'person', None)
        )
    return qs.exists()


@rules.predicate(bind=True)
def is_faculty_manager_for_partnership(self, user, partnership):
    return partnership.ucl_entity_id in self.context['role_qs'].get_entities_ids()


@rules.predicate(bind=True)
def is_faculty_manager_for_agreement(self, user, agreement):
    return (
            agreement.partnership.ucl_entity_id
            in self.context['role_qs'].get_entities_ids()
    )


@rules.predicate(bind=True)
def is_faculty_manager_for_ume(self, user, ucl_management_entity):
    return ucl_management_entity.entity_id in self.context['role_qs'].get_entities_ids()


@rules.predicate(bind=True)
def is_in_same_faculty_as_author(self, user, entity):
    other_user = entity.author.user
    return self.context['role_qs'].filter(
        Q(entity__partnershipentitymanager__person__user=other_user)
        | Q(entity__parent_of__entity__partnershipentitymanager__person__user=other_user)
    ).exists()


@rules.predicate
def entity_has_partnerships(user, entity):
    return entity.partnerships.exists()


@rules.predicate
def ume_has_partnerships(user, ucl_management_entity):
    return ucl_management_entity.entity.partnerships.exists()


@rules.predicate
def entity_has_children(user, partner_entity):
    return partner_entity.entity.parent_of.exists()


@rules.predicate(bind=True)
def partnership_type_allowed_for_user_scope(self, user, partnership_type):
    from .roles.partnership_manager import PartnershipEntityManager
    if self.context:
        qs = self.context['role_qs']
    else:
        qs = PartnershipEntityManager.objects.filter(
            person=getattr(user, 'person', None)
        )
    return any(partnership_type.name in role_row.scopes for role_row in qs)


@rules.predicate(bind=True)
def partnership_allowed_for_user_scope(self, user, partnership):
    return any(partnership.partnership_type in role_row.scopes
               for role_row in self.context['role_qs'])


@rules.predicate(bind=True)
def has_mobility_scope(self, user):
    return any(PartnershipType.MOBILITY.name in role_row.scopes
               for role_row in self.context['role_qs'])


@rules.predicate
def partnership_has_agreement(user, partnership):
    return partnership.agreements.exists()
