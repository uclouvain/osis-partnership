from partnership.models import AgreementStatus
from partnership.utils import user_is_adri, user_is_gf_of_faculty

__all__ = [
    'user_can_change_agreement',
    'user_can_delete_agreement',
]


def user_can_delete_agreement(user, agreement):
    return (
            agreement.status != AgreementStatus.VALIDATED.name
            and user_can_change_agreement(user, agreement)
    )


def user_can_change_agreement(user, agreement):
    if user_is_adri(user):
        return True
    return (
            agreement.status == AgreementStatus.WAITING.name
            and user_is_gf_of_faculty(user, agreement.partnership.ucl_entity)
    )
