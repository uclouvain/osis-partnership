from django import template

register = template.Library()


@register.filter
def can_change_partner_entity(user, entity):
    return entity.user_can_change(user)


@register.filter
def can_delete_partner_entity(user, entity):
    return entity.user_can_delete(user)


@register.filter
def can_change_ucl_management_entity(user, ucl_management_entity):
    return ucl_management_entity.user_can_change(user)


@register.filter
def can_delete_ucl_management_entity(user, ucl_management_entity):
    return ucl_management_entity.user_can_delete(user)
