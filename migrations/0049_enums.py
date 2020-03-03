# Generated by Django 2.2.5 on 2020-02-28 10:35
from django.db import migrations, models

mapping = {
    'PartnershipAgreement.status': {
        'waiting': 'WAITING',
        'validated': 'VALIDATED',
        'refused': 'REFUSED',
    },
    'Contact.title': {
        'mr': 'MISTER',
        'mme': 'MADAM',
    },
    'Media.visibility': {
        'public': 'PUBLIC',
        'staff': 'STAFF',
        'staff_student': 'STAFF_STUDENT',
    },
    'PartnershipYear.partnership_type': {
        'mobility': 'MOBILITY',
        'intention': 'INTENTION',
        'cadre': 'CADRE',
        'specifique': 'SPECIFIQUE',
        'codiplomation': 'CODIPLOMATION',
        'cotutelle': 'COTUTELLE',
        'fond_appuie': 'FOND_APPUIE',
        'autre': 'AUTRE',
    }
}


def update_values(apps, fn):
    for name, fields in mapping.items():
        model_name, field_name = name.split('.')
        model = apps.get_model('partnership', model_name)
        for value_from, value_to in fields.items():
            fn(model, value_from, value_to, field_name)


def forward(apps, schema_editor):
    update_values(
        apps,
        lambda model, v_from, v_to, name: model.objects.filter(
                **{name: v_from}
            ).update(
                **{name: v_to}
            )
    )


def reverse(apps, schema_editor):
    update_values(
        apps,
        lambda model, v_from, v_to, name: model.objects.filter(
                **{name: v_to}
            ).update(
                **{name: v_from}
            )
    )


class Migration(migrations.Migration):

    dependencies = [
        ('partnership', '0048_person_as_authors'),
    ]

    operations = [
        migrations.AlterField(
            model_name='partnershipagreement',
            name='status',
            field=models.CharField(choices=[('WAITING', 'status_waiting'), ('VALIDATED', 'status_validated'), ('REFUSED', 'status_refused')], default='WAITING', max_length=10, verbose_name='status'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='title',
            field=models.CharField(blank=True, choices=[('MISTER', 'mister'), ('MADAM', 'madame')], max_length=50, null=True, verbose_name='contact_title'),
        ),
        migrations.AlterField(
            model_name='media',
            name='visibility',
            field=models.CharField(choices=[('PUBLIC', 'visibility_public'), ('STAFF', 'visibility_staff'), ('STAFF_STUDENT', 'visibility_staff_student')], max_length=50, verbose_name='visibility'),
        ),
        migrations.AlterField(
            model_name='partnershipyear',
            name='partnership_type',
            field=models.CharField(choices=[('INTENTION', 'Déclaration d’intention'), ('CADRE', 'Accord-cadre'), ('SPECIFIQUE', 'Accord spécifique'), ('CODIPLOMATION', 'Accord de co-diplômation'), ('COTUTELLE', 'Accord de co-tutelle'), ('MOBILITY', 'Partenariat de mobilité'), ('FOND_APPUIE', 'Projet Fonds d’appuie à l’internationnalisation'), ('AUTRE', 'Autre')], max_length=255, verbose_name='partnership_type'),
        ),
        migrations.RunPython(forward, reverse),
    ]
