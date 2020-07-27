from django import template
from django.urls import reverse

from base.models.entity_version_address import EntityVersionAddress

register = template.Library()


@register.filter
def partner_media_download_url(partner, media):
    return reverse('partnerships:partners:medias:download', kwargs={
        'partner_pk': partner.pk,
        'pk': media.pk,
    })


@register.filter
def partnership_media_download_url(partnership, media):
    return reverse('partnerships:medias:download', kwargs={
        'partnership_pk': partnership.pk,
        'pk': media.pk,
    })


@register.filter
def address_one_line(address: EntityVersionAddress):
    if not address:
        return ''
    components = []
    if address.street:
        street = ''
        if address.street_number:
            street += address.street_number + ' '
        components.append(street + address.street)
    if address.postal_code:
        components.append(address.postal_code)
    if address.city:
        components.append(address.city)
    if address.state:
        components.append(address.state)
    if address.country:
        components.append(str(address.country).upper())
    return ', '.join(components)
