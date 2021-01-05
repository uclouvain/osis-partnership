import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('partnership', '0078_auto_20201205_1453'),
    ]

    operations = [
        migrations.AddField(
            model_name='partnership',
            name='description',
            field=models.TextField(blank=True, default='', help_text='visible_on_api', verbose_name='partnership_year_description'),
        ),
        migrations.AddField(
            model_name='partnership',
            name='id_number',
            field=models.CharField(default='', max_length=200, verbose_name='partnership_year_id_number'),
        ),
        migrations.AddField(
            model_name='partnership',
            name='missions',
            field=models.ManyToManyField(to='partnership.PartnershipMission', verbose_name='partnership_missions'),
        ),
        migrations.AddField(
            model_name='partnership',
            name='project_title',
            field=models.CharField(default='', max_length=200, verbose_name='partnership_year_project_title'),
        ),
        migrations.AddField(
            model_name='partnership',
            name='subtype',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='years', to='partnership.PartnershipSubtype', verbose_name='partnership_subtype'),
        ),
        migrations.AddField(
            model_name='partnership',
            name='ucl_status',
            field=models.CharField(choices=[('coordinator', 'Coordinator'), ('partner', 'Partner')], default='', max_length=20, verbose_name='partnership_year_ucl_status'),
        ),
    ]
