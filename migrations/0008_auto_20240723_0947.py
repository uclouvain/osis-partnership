# Generated by Django 3.2.25 on 2024-07-23 09:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('partnership', '0007_alter_media_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='partnership',
            name='all_student',
            field=models.BooleanField(blank=True, default=True, help_text='partnership_all_student_help_text',
                                      verbose_name='partnership_all_student'),
        ),
        migrations.AddField(
            model_name='partnership',
            name='diploma_by_ucl',
            field=models.CharField(blank=True,
                                   choices=[('UNIQUE', 'Partenaire unique'), ('SEPARED', 'Partenaire séparé'),
                                            ('NO_CODIPLOMA', 'Non co-diplômant')], max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='partnership',
            name='diploma_prod_by_ucl',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='partnership',
            name='partner_referent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                                    related_name='partner_referent', to='base.entity'),
        ),
        migrations.AddField(
            model_name='partnership',
            name='supplement_prod_by_ucl',
            field=models.CharField(blank=True, choices=[('YES', 'Oui'), ('NO', 'Non'), ('SHARED', 'Partagé')],
                                   max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='partnership',
            name='ucl_reference',
            field=models.BooleanField(blank=True, default=True, help_text='partnership_ucl_reference_help_text',
                                      verbose_name='partnership_ucl_reference'),
        ),
        migrations.AddField(
            model_name='partnershippartnerrelation',
            name='diploma_prod_by_partner',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='partnershippartnerrelation',
            name='diploma_with_ucl_by_partner',
            field=models.CharField(blank=True,
                                   choices=[('UNIQUE', 'Partenaire unique'), ('SEPARED', 'Partenaire séparé'),
                                            ('NO_CODIPLOMA', 'Non co-diplômant')], max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='partnershippartnerrelation',
            name='supplement_prod_by_partner',
            field=models.CharField(blank=True, choices=[('YES', 'Oui'), ('NO', 'Non'), ('SHARED', 'Partagé')],
                                   max_length=64, null=True),
        ),
    ]
