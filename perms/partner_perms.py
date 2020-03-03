from partnership.utils import user_is_adri, user_is_in_user_faculty, user_is_gf

__all__ = [
    'user_can_add_partner',
    'user_can_change_partner',
    'user_can_change_entity',
    'user_can_delete_entity',
]


def user_can_add_partner(user, partner=None):
    return user_is_adri(user) or user_is_gf(user)


def user_can_change_partner(user, partner=None):
    return user_is_adri(user)


def user_can_change_entity(user, entity):
    return user_is_adri(user) or user_is_in_user_faculty(user, entity.author.user)


def user_can_delete_entity(user, entity):
    return (
            user_can_change_entity(user, entity)
            and not entity.partnerships.exists()
            and not entity.childs.exists()
    )
