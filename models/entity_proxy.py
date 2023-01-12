# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################

from datetime import date

from django.db import models

from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.organization import Organization
from base.utils.cte import CTESubquery

__all__ = ['EntityProxy']


class EntityQuerySet(models.QuerySet):
    _last_version_qs = None

    def get_last_version(self):
        """Get the last version subquery for entity version"""
        if self._last_version_qs is None:
            self._last_version_qs = EntityVersion.objects.filter(
                entity=models.OuterRef('pk')
            ).order_by('-start_date')
        return self._last_version_qs

    def with_title(self):
        return self.annotate(
            title=models.Subquery(
                self.get_last_version().values('title')[:1]),
        )

    def with_acronym(self):
        return self.annotate(
            acronym=models.Subquery(
                self.get_last_version().values('acronym')[:1]),
        )

    def with_acronym_path(self):
        return self.annotate(
            acronym_path=CTESubquery(
                EntityVersion.objects.with_acronym_path(
                    entity_id=models.OuterRef('pk'),
                ).values('acronym_path')[:1]
            ),
        )

    def with_path_as_string(self):
        return self.annotate(
            path_as_string=CTESubquery(
                EntityVersion.objects.with_acronym_path(
                    entity_id=models.OuterRef('pk'),
                ).values('path_as_string')[:1],
                output_field=models.TextField()
            ),
        )

    def only_roots(self, at_date=None):
        return self.annotate(
            is_root=models.Exists(EntityVersion.objects.filter(
                entity_id=models.OuterRef('pk'),
            ).current(at_date or date.today()).only_roots()),
        ).filter(is_root=True)

    def only_valid(self):
        return self.annotate(
            is_valid=models.Exists(self.get_last_version().exclude(end_date__lte=date.today())),
        ).filter(is_valid=True)

    def ucl_entities(self):
        """UCL entities which have a partnership"""
        return self.filter(partnerships__isnull=False).distinct()

    def with_partner_info(self):
        from .partner.partner import Partner
        return self.annotate(
            partner_name=models.Subquery(Organization.objects.filter(
                pk=models.OuterRef('organization_id'),
            ).values('name')[:1]),
            partner_city=models.Subquery(Partner.objects.filter(
                pk=models.OuterRef('organization__partner__id'),
            ).annotate_address('city').values('city')[:1]),
            partner_country=models.Subquery(Partner.objects.filter(
                pk=models.OuterRef('organization__partner__id'),
            ).annotate_address('country__name').values('country_name')[:1]),
        )


class EntityManager(models.Manager.from_queryset(EntityQuerySet)):
    def partner_entities(self):
        """Partner entities which can be associated with partnerships (may be main entities or sub-entities)"""
        return self.get_queryset().filter(organization__partner__isnull=False)

    def partners_having_partnership(self):
        """Partner entities which have partnerships (may be main entities or sub-entities)"""
        return self.get_queryset().filter(partner_of__isnull=False).distinct()

    def year_entities(self):
        return self.get_queryset().filter(partnerships_years__isnull=False).distinct()

    def children_of_partner(self, partner):
        """Partner sub-entities of partner"""
        return self.get_queryset().filter(
            entityversion__parent__organization__partner=partner,
        )

    def ucl_entities_parents(self):
        """UCL entity parents which children have a partnership"""
        cte = EntityVersion.objects.with_children(entity__partnerships__isnull=False)
        qs = cte.queryset().with_cte(cte).values('entity_id')
        return self.get_queryset().filter(pk__in=qs)


class EntityProxy(Entity):
    """Proxy model of base.Entity"""
    objects = EntityManager()

    class Meta:
        proxy = True
