from django import template

register = template.Library()


@register.filter
def can_change_partner_entity(user, entity):
    return entity.user_can_change(user)


@register.filter
def can_delete_partner_entity(user, entity):
    return entity.user_can_delete(user)
