from partnership.utils import user_is_adri, user_is_gf_of_faculty, user_is_gf

__all__ = [
    'user_can_read_ucl_management_entity',
    'user_can_delete_ucl_management_entity',
    'user_can_change_ucl_management_entity',
    'user_can_list_ucl_management_entity',
    'user_can_create_ucl_management_entity',
]


def user_can_read_ucl_management_entity(user, ume):
    return user_is_adri(user) or user_is_gf_of_faculty(user, ume.faculty)


def user_can_change_ucl_management_entity(user, ume):
    return user_is_adri(user) or user_is_gf_of_faculty(user, ume.faculty)


def user_can_delete_ucl_management_entity(user, ume):
    return user_is_adri(user) and not ume.has_linked_partnerships()


def user_can_list_ucl_management_entity(user, ume=None):
    return user_is_adri(user) or user_is_gf(user)


def user_can_create_ucl_management_entity(user, ume=None):
    return user_is_adri(user)
