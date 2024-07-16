from django.db import models
from django.db.models import OuterRef, Subquery, Q
from django.db.models.functions import Now

from base.models.entity_version import EntityVersion
from base.utils.cte import CTESubquery
from partnership.models import Financing, AgreementStatus, PartnershipType, PartnershipDiplomaWithUCL, \
    PartnershipProductionSupplement

__all__ = ['PartnershipPartnerRelation']


class PartnershipPartnerRelationQuerySet(models.QuerySet):
    def add_acronym_path(self):
        ref = models.OuterRef('partnership__ucl_entity_id')

        return self.annotate(
            acronym_path=CTESubquery(
                EntityVersion.objects.with_acronym_path(
                    entity_id=ref
                ).values('acronym_path')[:1]
            ),
        )

    def annotate_partner_address(self, *fields):
        """
        Add annotations on partner contact address

        :param fields: list of fields relative to EntityVersionAddress
            If a field contains a traversal, e.g. country__name, it will be
            available as country_name
        """
        contact_address_qs = EntityVersion.objects.filter(
            entity__organization=OuterRef('entity__organization'),
            parent__isnull=True,
        ).order_by('-start_date')
        qs = self
        for field in fields:
            lookup = Subquery(contact_address_qs.values(
                'entityversionaddress__{}'.format(field)
            )[:1])
            qs = qs.annotate(**{field.replace('__', '_'): lookup})
        return qs

    def annotate_financing(self, academic_year):
        """
        Add annotations to get funding for an academic year based on country
        """
        return self.annotate(
            financing_source=Subquery(Financing.objects.filter(
                countries=OuterRef('country_id'),
                academic_year=academic_year,
            ).values('type__program__source__name')[:1]),
            financing_program=Subquery(Financing.objects.filter(
                countries=OuterRef('country_id'),
                academic_year=academic_year,
            ).values('type__program__name')[:1]),
            financing_type=Subquery(Financing.objects.filter(
                countries=OuterRef('country_id'),
                academic_year=academic_year,
            ).values('type__name')[:1]),
        )

    def filter_for_api(self, academic_year):
        from partnership.models import PartnershipYear, PartnershipAgreement
        return self.annotate(
            current_academic_year=models.Value(
                academic_year.id, output_field=models.AutoField()
            ),
        ).alias(
            has_years_in=models.Exists(
                PartnershipYear.objects.filter(
                    partnership=OuterRef('partnership_id'),
                    academic_year=academic_year,
                )
            ),
            has_valid_agreement_in_current_year=models.Exists(
                PartnershipAgreement.objects.filter(
                    partnership=OuterRef('partnership_id'),
                    status=AgreementStatus.VALIDATED.name,
                    start_academic_year__year__lte=academic_year.year,
                    end_academic_year__year__gte=academic_year.year,
                )
            ),
        ).filter(
            # If mobility, should have agreement for current year
            # and have a partnership year for current year
            Q(
                partnership__partnership_type=PartnershipType.MOBILITY.name,
                has_valid_agreement_in_current_year=True,
                has_years_in=True,
            )
            # Else all other types do not need agreement
            | (
                    ~Q(partnership__partnership_type=PartnershipType.MOBILITY.name)
                    & Q(partnership__end_date__gte=Now())
            ),
            # And must be public
            partnership__is_public=True,
        )


class PartnershipPartnerRelation(models.Model):
    """
    Le modèle représentant une relation entre une entité et un partenariat
    """
    partnership = models.ForeignKey(
        'partnership.Partnership',
        on_delete=models.CASCADE,
    )
    entity = models.ForeignKey(
        'base.Entity',
        related_name='partner_of',
        on_delete=models.PROTECT,
    )

    diploma_with_ucl_by_partner = models.CharField(
        max_length=64,
        choices=PartnershipDiplomaWithUCL.choices(),
        null=True,
        blank=True
    )
    diploma_prod_by_partner = models.BooleanField(
        default=False
    )
    supplement_prod_by_partner = models.CharField(
        max_length=64,
        choices=PartnershipProductionSupplement.choices(),
        null=True,
        blank=True
    )

    objects = PartnershipPartnerRelationQuerySet.as_manager()

    class Meta:
        unique_together = ['partnership', 'entity']
