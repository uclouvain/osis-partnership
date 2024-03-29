# Generated by Django 2.2.5 on 2020-02-18 10:29

from django.db import migrations, models
import django.db.models.deletion


def link_author_person(apps, schema_editor):
    Person = apps.get_model('base', 'Person')
    Media = apps.get_model('partnership', 'Media')
    Partner = apps.get_model('partnership', 'Partner')
    PartnerEntity = apps.get_model('partnership', 'PartnerEntity')
    Partnership = apps.get_model('partnership', 'Partnership')

    for model in [Media, Partner, PartnerEntity, Partnership]:
        persons = Person.objects.filter(
            user_id=models.OuterRef('author_id')
        ).values_list('id')[:1]
        model.objects.update(
            new_author_id=models.Subquery(persons)
        )


def link_person_author(apps, schema_editor):
    Person = apps.get_model('base', 'Person')
    Media = apps.get_model('partnership', 'Media')
    Partner = apps.get_model('partnership', 'Partner')
    PartnerEntity = apps.get_model('partnership', 'PartnerEntity')
    Partnership = apps.get_model('partnership', 'Partnership')

    for model in [Media, Partner, PartnerEntity, Partnership]:
        persons = Person.objects.filter(
            id=models.OuterRef('new_author_id'),
        ).values_list('user_id')[:1]
        model.objects.update(
            author_id=models.Subquery(persons)
        )


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0505_update_summary_submission_calendars'),
        ('partnership', '0047_nullable_authors'),
    ]

    operations = [
        migrations.AddField(
            model_name='media',
            name='new_author',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='base.Person', verbose_name='author'),
        ),
        migrations.AddField(
            model_name='partner',
            name='new_author',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='base.Person', verbose_name='author'),
        ),
        migrations.AddField(
            model_name='partnerentity',
            name='new_author',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='base.Person', verbose_name='author'),
        ),
        migrations.AddField(
            model_name='partnership',
            name='new_author',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='base.Person', verbose_name='author'),
        ),
        migrations.RunPython(
            link_author_person, link_person_author, elidable=True
        ),
        migrations.RemoveField(
            model_name='media',
            name='author',
        ),
        migrations.RemoveField(
            model_name='partner',
            name='author',
        ),
        migrations.RemoveField(
            model_name='partnerentity',
            name='author',
        ),
        migrations.RemoveField(
            model_name='partnership',
            name='author',
        ),
        migrations.RenameField(
            model_name='media',
            old_name='new_author',
            new_name='author',
        ),
        migrations.RenameField(
            model_name='partner',
            old_name='new_author',
            new_name='author',
        ),
        migrations.RenameField(
            model_name='partnerentity',
            old_name='new_author',
            new_name='author',
        ),
        migrations.RenameField(
            model_name='partnership',
            old_name='new_author',
            new_name='author',
        ),
    ]
