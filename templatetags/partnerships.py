from django import template

register = template.Library()


@register.filter
def can_change_partner_entity(user, entity):
    return entity.user_can_change(user)


@register.filter
def can_delete_partner_entity(user, entity):
    return entity.user_can_delete(user)


@register.filter
def can_change_agreement(user, agreement):
    return agreement.user_can_change(user)


@register.filter
def can_change_management_entity(user, management_entity):
    return management_entity.user_can_change(user)


@register.filter
def can_delete_management_entity(user, management_entity):
    return management_entity.user_can_delete(user)
