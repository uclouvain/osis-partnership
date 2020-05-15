import rules

from partnership.utils import (
    user_is_adri, user_is_gf, user_is_gf_of_faculty,
    user_is_in_user_faculty,
)


@rules.predicate
def is_validated(user, agreement):
    from partnership.models import AgreementStatus
    return agreement.status == AgreementStatus.VALIDATED.name


@rules.predicate
def is_waiting(user, agreement):
    from partnership.models import AgreementStatus
    return agreement.status == AgreementStatus.WAITING.name


@rules.predicate
def is_adri(user):
    return user_is_adri(user)


@rules.predicate
def is_faculty_manager(user, obj=None):
    if obj is None:
        return user_is_gf(user)

    from partnership.models import (
        Partnership, PartnershipAgreement, PartnershipType,
        UCLManagementEntity, Partner,
    )
    entity = None

    if isinstance(obj, PartnershipAgreement):
        entity = obj.partnership.ucl_entity
    elif isinstance(obj, Partnership):
        entity = obj.ucl_entity
    elif isinstance(obj, UCLManagementEntity):
        entity = obj.entity
    elif isinstance(obj, (PartnershipType, Partner)):
        return user_is_gf(user)

    if entity is None:
        raise NotImplementedError(
            "Predicate not handled for type {} or object {} "
            "has no related entity".format(type(obj), repr(obj))
        )
    return user_is_gf_of_faculty(user, entity)


@rules.predicate
def is_in_same_faculty_as_author(user, entity):
    return user_is_in_user_faculty(user, entity.author.user)


@rules.predicate
def is_mobility(user, obj):
    from partnership.models import Partnership, PartnershipType

    if isinstance(obj, Partnership):
        return obj.partnership_type == PartnershipType.MOBILITY.name
    elif isinstance(obj, PartnershipType):
        return obj == PartnershipType.MOBILITY


@rules.predicate
def manage_type(user, obj):
    from partnership.models import Partnership
    from partnership.models import PartnershipType

    partnership_type = obj
    if isinstance(obj, Partnership):
        partnership_type = obj.partnership_type
    elif isinstance(obj, PartnershipType):
        partnership_type = partnership_type.name
    return user.has_perm('partnership.change_%s' % partnership_type)


@rules.predicate
def has_partnerships(user, entity):
    from partnership.models import UCLManagementEntity

    if isinstance(entity, UCLManagementEntity):
        return entity.entity.partnerships.exists()

    return entity.partnerships.exists()


@rules.predicate
def has_children(user, entity):
    return entity.childs.exists()
