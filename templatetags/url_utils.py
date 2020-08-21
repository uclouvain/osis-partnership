from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def full_uri(context, url):
    return context['request'].build_absolute_uri(url)
