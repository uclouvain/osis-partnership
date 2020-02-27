from django.db import models

__all__ = ['PartnershipEntityManager']


class PartnershipEntityManager(models.Model):
    """
    Remplace PersonEntity et ManagementEntity dans le cadre de partnership.

    Utilisé à l'origine pour séparer les permissions des partenariats du reste d'OSIS.
    """
    person = models.ForeignKey('base.Person', on_delete=models.CASCADE)
    entity = models.ForeignKey('base.Entity', on_delete=models.CASCADE)

    def __str__(self):
        return '{} {}'.format(self.person, self.entity)
