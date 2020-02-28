from partnership.utils import user_is_adri, user_is_gf_of_faculty, user_is_gf

__all__ = [
    'user_can_change_partnership',
    'user_can_add_partnership',
]


def user_can_change_partnership(user, partnership):
    if user_is_adri(user):
        return True
    return user_is_gf_of_faculty(user, partnership.ucl_university)


def user_can_add_partnership(user, partnership=None):
    return user_is_adri(user) or user_is_gf(user)
