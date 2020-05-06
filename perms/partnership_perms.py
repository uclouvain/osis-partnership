from partnership.models import PartnershipType
from partnership.utils import user_is_adri, user_is_gf_of_faculty, user_is_gf

__all__ = [
    'user_can_change_partnership',
    'user_can_add_partnership',
]


def user_can_change_partnership(user, partnership):
    """
    :param user: Current user
    :type partnership: partnership.models.Partnership
    """
    if not user.has_perm('partnership.can_access_partnerships'):
        return False
    partnership_type = partnership.partnership_type
    if partnership_type == PartnershipType.MOBILITY.name:
        return (
                user_is_adri(user)
                or user_is_gf_of_faculty(user, partnership.ucl_entity)
        )
    return user.has_perm('partnership.change_%s' % partnership_type)


def user_can_add_partnership(user, partnership_type):
    """
    :param user: Current user
    :type partnership_type: PartnershipType
    """
    if not user.has_perm('partnership.can_access_partnerships'):
        return False
    if partnership_type == PartnershipType.MOBILITY:
        return user_is_adri(user) or user_is_gf(user)
    return user.has_perm('partnership.change_%s' % partnership_type.name)
