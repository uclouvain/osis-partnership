# Generated by Django 3.2.12 on 2022-09-22 10:04

from django.db import migrations
from django.db.models import Func, F, Value

urls_to_migrate = [
    # Accord mobilite migration
    {
        'from': 'https://alfresco.uclouvain.be/alfresco/webdav/UCL/Services%20généraux/ADRI/ucl_personnel/accords_mobilite/',
        'to': 'https://uclouvain.sharepoint.com/sites/RFM/Partenariats/Accords/',
    },
    {
        'from': 'https://alfresco.uclouvain.be/alfresco/webdav/UCL/Services%20généraux/ADRI/ucl_personnel/accords_mobilite/',
        'to': 'https://uclouvain.sharepoint.com/sites/RFM/Partenariats/Accords/',
    },
    {
        'from': 'https://alfresco.uclouvain.be/alfresco/webdav/UCL/Services%20g%C3%A9n%C3%A9raux/ADRI/ucl_personnel/accords_mobilite/',
        'to': 'https://uclouvain.sharepoint.com/sites/RFM/Partenariats/Accords/',
    },

    # Evaluation migration
    {
        'from': 'https://alfresco.uclouvain.be/alfresco/webdav/UCL/Services%20g%C3%A9n%C3%A9raux/ADRI/UCL_personnel/eval2017/',
        'to': 'https://uclouvain.sharepoint.com/sites/RFM/Partenariats/Archivage/Evaluations/',
    },
    {
        'from': 'https://alfresco.uclouvain.be/alfresco/webdav/UCL/Services généraux/ADRI/UCL_personnel/eval2017/',
        'to': 'https://uclouvain.sharepoint.com/sites/RFM/Partenariats/Archivage/Evaluations/',
    },
    {
        'from': 'https://alfresco.uclouvain.be/alfresco/webdav/UCL/Services généraux/ADRI/UCL_personnel/eval2013/',
        'to': 'https://uclouvain.sharepoint.com/sites/RFM/Partenariats/Archivage/Evaluations/2013/',
    },
    {
        'from': 'https://alfresco.uclouvain.be/alfresco/webdav/UCL/Services généraux/ADRI/UCL_personnel/eval/',
        'to': 'https://uclouvain.sharepoint.com/sites/RFM/Partenariats/Archivage/Evaluations/2010/',
    },

    # Flux migration
    {
        'from': 'https://alfresco.uclouvain.be/alfresco/webdav/UCL/Services%20g%C3%A9n%C3%A9raux/ADRI/UCL_personnel_et_etudiants/flux_2020/',
        'to': 'https://uclouvain.sharepoint.com/sites/RFM/Partenariats/Flux/',
    },

    # Stat BW
    {
        'from': 'https://alfresco.uclouvain.be/alfresco/webdav/UCL/Services%20g%C3%A9n%C3%A9raux/ADRI/ucl_personnel/stats_bw/CA%20FREDERI01_2018-2013.pdf',
        'to': 'https://uclouvain.sharepoint.com/sites/RFM/Partenariats/Flux/CA%20FREDERI01_2018-2013.pdf'
    },
    {
        'from': 'https://alfresco.uclouvain.be/alfresco/webdav/UCL/Services%20g%C3%A9n%C3%A9raux/ADRI/UCL_personnel/eval/A%20%20WIEN01.pdf',
        'to': 'https://uclouvain.sharepoint.com/sites/RFM/Partenariats/Archivage/Evaluations/A%20%20WIEN01.pdf'
    }
]


def update_medias_url(apps, schema_editor):
    Media = apps.get_model('partnership', 'Media')
    for url in urls_to_migrate:
        Media.objects.filter(url__startswith=url['from']).update(
            url=Func(
                F('url'),
                Value(url['from']), Value(url['to']),
                function='replace',
            )
        )


def reverse_medias_url(apps, schema_editor):
    Media = apps.get_model('partnership', 'Media')
    for url in urls_to_migrate:
        Media.objects.filter(url__startswith=url['to']).update(
            url=Func(
                F('url'),
                Value(url['to']), Value(url['from']),
                function='replace',
            )
        )


class Migration(migrations.Migration):

    dependencies = [
        ('partnership', '0002_auto_20220610_1621'),
    ]

    operations = [
        migrations.RunPython(update_medias_url, reverse_code=reverse_medias_url, elidable=True),
    ]