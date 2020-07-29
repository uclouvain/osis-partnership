import requests
from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.management import BaseCommand

from base.models.entity_version_address import EntityVersionAddress
from partnership.management.commands.progress_bar import ProgressBarMixin


class Command(ProgressBarMixin, BaseCommand):

    def handle(self, *args, **options):
        # Fill the address for the partners only
        queryset = EntityVersionAddress.objects.filter(
            location__isnull=True,
            entity_version__entity__organization__partner__isnull=False,
        ).select_related('country')

        count = queryset.count()

        self.print_progress_bar(0, count)

        # To prevent too many requests to geocoding, maintain a cache
        cache = {}
        not_found = []
        obj_list = []
        for i, address in enumerate(queryset):
            parts = [
                address.street_number,
                address.street,
                address.postal_code,
                address.city,
                address.state,
                address.country.name if address.country else '',
            ]
            search = ' '.join(filter(None, parts))
            if not search:
                continue

            if search not in cache:
                response = requests.get(settings.GEOCODING_URL, {
                    'address': search,
                }, headers={
                    'Authorization': 'Bearer {}'.format(settings.GEOCODING_TOKEN),
                })
                try:
                    location = response.json()['results'][0]['geometry']['location']
                    address.location = cache[search] = Point(
                        location['lng'],
                        location['lat'],
                    )
                except IndexError:
                    address.location = cache[search] = None
                    not_found.append(search)
            else:
                address.location = cache[search]
            obj_list.append(address)
            self.print_progress_bar(i, count)

        self.stdout.write('')
        self.stdout.write("{} updated, {} not found".format(
            len(obj_list),
            len(not_found),
        ))

        EntityVersionAddress.objects.bulk_update(obj_list, fields=['location'])
