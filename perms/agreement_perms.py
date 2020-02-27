from partnership.models import PartnershipAgreement
from partnership.utils import user_is_adri, user_is_gf_of_faculty

__all__ = [
    'user_can_change_agreement',
    'user_can_delete_agreement',
]


def user_can_delete_agreement(user, agreement):
    return agreement.status != PartnershipAgreement.STATUS_VALIDATED and user_can_change_agreement(user, agreement)


def user_can_change_agreement(user, agreement):
    if user_is_adri(user):
        return True
    return (
            agreement.status == agreement.STATUS_WAITING
            and user_is_gf_of_faculty(user, agreement.partnership.ucl_university)
    )
