# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-06-07 14:37
from __future__ import unicode_literals

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('reference', '0017_language_changed'),
        ('osis_common', '0014_messagequeuecache'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('base', '0283_learningunityear_existing_proposal_in_epc'),
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='address_name_help_text', max_length=255, verbose_name='name')),
                ('address', models.TextField(verbose_name='address')),
                ('postal_code', models.CharField(blank=True, max_length=20, null=True, verbose_name='postal_code')),
                ('city', models.CharField(blank=True, max_length=255, null=True, verbose_name='city')),
                ('city_french', models.CharField(blank=True, max_length=255, null=True, verbose_name='city_french')),
                ('city_english', models.CharField(blank=True, max_length=255, null=True, verbose_name='city_english')),
                ('country', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='reference.Country', verbose_name='country')),
            ],
        ),
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(choices=[('mr', 'mister'), ('mme', 'madame')], max_length=50, verbose_name='contact_title')),
                ('last_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='last_name')),
                ('first_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='first_name')),
                ('society', models.CharField(blank=True, max_length=255, null=True, verbose_name='society')),
                ('function', models.CharField(blank=True, max_length=255, null=True, verbose_name='function')),
                ('phone', models.CharField(blank=True, max_length=255, null=True, verbose_name='phone')),
                ('mobile_phone', models.CharField(blank=True, max_length=255, null=True, verbose_name='mobile_phone')),
                ('fax', models.CharField(blank=True, max_length=255, null=True, verbose_name='fax')),
                ('email', models.EmailField(blank=True, max_length=254, null=True, verbose_name='email')),
                ('comment', models.TextField(blank=True, default='', verbose_name='comment')),
            ],
        ),
        migrations.CreateModel(
            name='ContactType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'ordering': ('value',),
            },
        ),
        migrations.CreateModel(
            name='Media',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('description', models.TextField(blank=True, default='', verbose_name='description')),
                ('url', models.URLField(blank=True, null=True, verbose_name='url')),
                ('visibility', models.CharField(choices=[('public', 'visibility_public'), ('staff', 'visibility_staff'), ('staff_student', 'visibility_staff_student')], max_length=50, verbose_name='visibility')),
                ('document_file', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='osis_common.DocumentFile', verbose_name='document')),
            ],
        ),
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
                ('author', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='author')),
                ('contact_address', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='partnership.Address', verbose_name='address')),
                ('medias', models.ManyToManyField(blank=True, related_name='_partner_medias_+', to='partnership.Media', verbose_name='medias')),
                ('now_known_as', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='formely_known_as', to='partnership.Partner', verbose_name='now_known_as')),
            ],
            options={
                'ordering': ('-created',),
                'permissions': (('can_access_partners', 'can_access_partners'),),
            },
        ),
        migrations.CreateModel(
            name='PartnerEntity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('comment', models.TextField(blank=True, default='', verbose_name='comment')),
                ('created', models.DateField(auto_now_add=True, verbose_name='created')),
                ('modified', models.DateField(auto_now=True, verbose_name='modified')),
                ('address', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='partnership.Address', verbose_name='address')),
                ('author', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='author')),
                ('contact_in', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='partnership.Contact', verbose_name='contact_in')),
                ('contact_out', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='partnership.Contact', verbose_name='contact_out')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='childs', to='partnership.PartnerEntity', verbose_name='parent_entity')),
                ('partner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entities', to='partnership.Partner', verbose_name='partner')),
            ],
            options={
                'ordering': ('name',),
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
                ('author', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='author')),
                ('contacts', models.ManyToManyField(blank=True, related_name='_partnership_contacts_+', to='partnership.Contact', verbose_name='contacts')),
                ('partner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='partnerships', to='partnership.Partner', verbose_name='partner')),
                ('partner_entity', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='partnerships', to='partnership.PartnerEntity', verbose_name='partner_entity')),
            ],
            options={
                'ordering': ('-created',),
                'permissions': (('can_access_partners', 'can_access_partnerships'),),
            },
        ),
        migrations.CreateModel(
            name='PartnershipTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'ordering': ('value',),
            },
        ),
        migrations.CreateModel(
            name='PartnershipType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'ordering': ('value',),
            },
        ),
        migrations.CreateModel(
            name='PartnerTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'ordering': ('value',),
            },
        ),
        migrations.CreateModel(
            name='PartnerType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'ordering': ('value',),
            },
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
            model_name='partnership',
            name='ucl_university',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='partnerships', to='base.EntityVersion', verbose_name='partner_entity'),
        ),
        migrations.AddField(
            model_name='partnership',
            name='ucl_university_labo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='base.EntityVersion', verbose_name='partner_entity'),
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
        migrations.AddField(
            model_name='contact',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='partnership.ContactType', verbose_name='contact_type'),
        ),
    ]
