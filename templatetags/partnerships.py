from django import template
from django.conf import settings
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


@register.simple_tag
def static_map_url(location, zoom=3, width=300, height=250, marker_name='pin-l'):
    if not location:
        return ''
    return (
        "https://api.mapbox.com/styles/v1/mapbox/streets-v11/static/"
        "{marker_name}({lon},{lat})/{lon},{lat},{zoom}/{width}x{height}"
        "?access_token={token}".format(
            marker_name=marker_name,
            lon=location.x,
            lat=location.y,
            zoom=zoom,
            width=width,
            height=height,
            token=settings.MAPBOX['ACCESS_TOKEN'],
        )
    )
