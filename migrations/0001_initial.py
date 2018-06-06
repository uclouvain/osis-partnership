# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-05-31 12:31
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Partner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_valid', models.BooleanField(default=False, verbose_name='is_valid')),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('is_ies', models.BooleanField(default=False, verbose_name='is_ies')),
                ('partner_code', models.CharField(max_length=255, unique=True, verbose_name='partner_code')),
                ('pic_code', models.CharField(max_length=255, unique=True, verbose_name='pic_code')),
                ('erasmus_code', models.CharField(max_length=255, unique=True, verbose_name='erasmus_code')),
                ('start_date', models.DateField(blank=True, null=True, verbose_name='start_date')),
                ('end_date', models.DateField(blank=True, null=True, verbose_name='end_date')),
                ('website', models.URLField(verbose_name='website')),
                ('email', models.EmailField(blank=True, max_length=254, null=True, verbose_name='email')),
                ('phone', models.CharField(blank=True, max_length=255, null=True, verbose_name='phone')),
                ('is_nonprofit', models.NullBooleanField(verbose_name='is_nonprofit')),
                ('is_public', models.NullBooleanField(verbose_name='is_public')),
                ('contact_type', models.CharField(blank=True, max_length=255, null=True, verbose_name='organisation_type')),
                ('use_egracons', models.BooleanField(default=False, verbose_name='use_egracons')),
                ('comment', models.TextField(blank=True, default='', verbose_name='comment')),
                ('created', models.DateField(auto_now_add=True, verbose_name='created')),
                ('modified', models.DateField(auto_now=True, verbose_name='modified')),
                ('author', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='author')),
                ('now_known_as', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='old_partners', to='partnership.Partner', verbose_name='new_partner')),
            ],
            options={
                'permissions': (('can_access_partners', 'can_access_partners'),),
            },
        ),
        migrations.CreateModel(
            name='Partnership',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_valid', models.BooleanField(default=False, verbose_name='is_valid')),
                ('start_date', models.DateField(blank=True, null=True, verbose_name='start_date')),
                ('end_date', models.DateField(blank=True, null=True, verbose_name='end_date')),
                ('mobility_type', models.CharField(choices=[('SMS', 'mobility_type_sms'), ('SMP', 'mobility_type_smp'), ('STA', 'mobility_type_sta'), ('STT', 'mobility_type_stt'), ('NA', 'mobility_type_na')], max_length=255, verbose_name='mobility_type')),
                ('comment', models.TextField(blank=True, default='', verbose_name='comment')),
                ('created', models.DateField(auto_now_add=True, verbose_name='created')),
                ('modified', models.DateField(auto_now=True, verbose_name='modified')),
                ('author', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='author')),
                ('partner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='partnerships', to='partnership.Partner', verbose_name='partner')),
            ],
            options={
                'permissions': (('can_access_partners', 'can_access_partnerships'),),
            },
        ),
        migrations.CreateModel(
            name='PartnershipTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='PartnershipType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='PartnerTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='PartnerType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='partnership',
            name='partner_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='partnerships', to='partnership.PartnershipType', verbose_name='partnership_type'),
        ),
        migrations.AddField(
            model_name='partnership',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='partnerships', to='partnership.PartnershipTag', verbose_name='tags'),
        ),
        migrations.AddField(
            model_name='partner',
            name='partner_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='partners', to='partnership.PartnerType', verbose_name='partner_type'),
        ),
        migrations.AddField(
            model_name='partner',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='partners', to='partnership.PartnerTag', verbose_name='tags'),
        ),
    ]
