# Generated by Django 2.2.10 on 2020-05-11 11:41
import json

from django.db import migrations, models
import django.db.models.deletion
from django.db.models import OuterRef, Subquery, Exists


def forward(apps, schema_editor):
    # Apply the fixtures, we can't use call_command('loaddata') because the
    # model might change
    fixtures = [
        'partnership/fixtures/funding_source.json',
        'partnership/fixtures/funding_program.json',
        'partnership/fixtures/funding_type.json',
    ]
    for fixture in fixtures:
        with open(fixture) as f:
            data = json.load(f)
            model = apps.get_model(data[0]['model'])
            for datum in data:
                fields = {k + ('_id' if k in ['source', 'program'] else ''): v
                          for k, v in datum['fields'].items()}
                model.objects.create(
                    **fields,
                )

    FundingProgram = apps.get_model('partnership', 'FundingProgram')
    FundingType = apps.get_model('partnership', 'FundingType')
    Financing = apps.get_model('partnership', 'Financing')
    # Create the default funding program
    default_program = FundingProgram.objects.create(
        name="Néant",
        source_id=10,  # This is the source "Néant" from fixture
    )

    # Create funding type for every name/url couple if not already existing
    couples = Financing.objects.annotate(
        matching_type=Exists(FundingType.objects.filter(
            name__iexact=OuterRef('name'),
        )),
    ).filter(
        matching_type=False,
    ).distinct('name', 'url').order_by('name', 'url').values('name', 'url')

    funding_types = []
    for couple in couples:
        funding_types.append(FundingType(
            name=couple['name'],
            url=couple['url'] or '',
            program=default_program,
        ))
    FundingType.objects.bulk_create(funding_types)

    # Add them to the existing financing
    Financing.objects.update(
        type_id=Subquery(
            FundingType.objects.filter(
                name__iexact=OuterRef('name'),
            ).values('pk')[:1]
        )
    )


def backward(apps, schema_editor):
    FundingType = apps.get_model('partnership', 'FundingType')
    Financing = apps.get_model('partnership', 'Financing')

    # Fill the values of name/url with corresponding funding type
    qs = FundingType.objects.filter(pk=OuterRef('type_id'))
    Financing.objects.update(
        name=Subquery(qs.values('name')[:1]),
        url=Subquery(qs.values('url')[:1]),
    )


class Migration(migrations.Migration):
    dependencies = [
        ('base', '0513_auto_20200424_1417'),
        ('partnership', '0056_media_url_maxlength'),
    ]

    operations = [
        migrations.CreateModel(
            name='FundingProgram',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID',
                )),
                ('name', models.CharField(
                    max_length=100,
                    verbose_name='funding_program',
                )),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='FundingSource',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID',
                )),
                ('name', models.CharField(
                    max_length=100,
                    verbose_name='funding_source',
                )),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='FundingType',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID',
                )),
                ('name', models.CharField(
                    max_length=100,
                    verbose_name='funding_type',
                )),
                ('url', models.URLField(verbose_name='url')),
                ('program', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='partnership.FundingProgram',
                    verbose_name='funding_program',
                )),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.AddField(
            model_name='fundingprogram',
            name='source',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='partnership.FundingSource',
                verbose_name='funding_source',
            ),
        ),
        migrations.AddField(
            model_name='financing',
            name='type',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='partnership.FundingType',
                verbose_name='funding_type'
            ),
        ),
        migrations.AddField(
            model_name='partnershipyear',
            name='funding_type',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='years',
                to='partnership.FundingType',
                verbose_name='funding_type',
            ),
        ),
        migrations.AlterUniqueTogether(
            name='financing',
            unique_together={('type', 'academic_year')},
        ),
        migrations.AlterField(
            model_name='financing',
            name='name',
            field=models.CharField(verbose_name='name', max_length=100, null=True)
        ),
        migrations.AlterField(
            model_name='financing',
            name='url',
            field=models.URLField(verbose_name='url', null=True)
        ),
        migrations.RunPython(forward, backward),
        migrations.RemoveField(
            model_name='financing',
            name='name',
        ),
        migrations.RemoveField(
            model_name='financing',
            name='url',
        ),
        migrations.AlterField(
            model_name='financing',
            name='type',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='partnership.FundingType',
                verbose_name='funding_type'
            ),
        ),
    ]
