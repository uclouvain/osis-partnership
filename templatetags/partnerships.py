from django import template

register = template.Library()


@register.filter
def can_change_partner_entity(user, entity):
    return entity.user_can_change(user)
