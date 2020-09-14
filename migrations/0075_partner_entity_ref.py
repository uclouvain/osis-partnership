from django.db import migrations, models
import django.db.models.deletion
from django.db.models import F, Subquery, OuterRef


def forward(apps, schema_editor):
    PartnerEntity = apps.get_model('partnership', 'PartnerEntity')
    EntityVersion = apps.get_model('base', 'EntityVersion')

    PartnerEntity.objects.annotate(
        fetched_entity_id=Subquery(EntityVersion.objects.filter(
            pk=OuterRef('entity_version'),
        ).values('entity_id')[:1]),
    ).update(entity_id=F('fetched_entity_id'))


class Migration(migrations.Migration):
    dependencies = [
        ('base', '0535_auto_20200908_1239'),
        ('partnership', '0074_performance'),
    ]

    operations = [
        migrations.AddField(
            model_name='partnerentity',
            name='entity',
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='base.Entity',
                verbose_name='partner',
            ),
        ),
        migrations.RunPython(forward, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='partnerentity',
            name='entity_version',
        ),
        migrations.AlterField(
            model_name='partnerentity',
            name='entity',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.PROTECT,
                to='base.Entity',
                verbose_name='partner',
            ),
        ),
    ]
