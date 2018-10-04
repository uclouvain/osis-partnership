# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-05 14:25
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('partnership', '0011_auto_20180705_1231'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='partnership.ContactType', verbose_name='contact_type'),
        ),
        migrations.AlterField(
            model_name='partner',
            name='contact_type',
            field=models.CharField(blank=True, choices=[('EPLUS-EDU-HEI', 'Higher education institution (tertiary level)'), ('EPLUS-EDU-GEN-PRE', 'School/Institute/Educational centre – General education (pre-primary level)'), ('EPLUS-EDU-GEN-PRI', 'School/Institute/Educational centre – General education (primary level)'), ('EPLUS-EDU-GEN-SEC', 'School/Institute/Educational centre – General education (secondary level)'), ('EPLUS-EDU-VOC-SEC', 'School/Institute/Educational centre – Vocational Training (secondary level)'), ('EPLUS-EDU-VOC-TER', 'School/Institute/Educational centre – Vocational Training (tertiary level)'), ('EPLUS-EDU-ADULT', 'School/Institute/Educational centre – Adult education'), ('EPLUS-BODY-PUB-NAT', 'National Public body'), ('EPLUS-BODY-PUB-REG', 'Regional Public body'), ('EPLUS-BODY-PUB-LOC', 'Local Public body'), ('EPLUS-ENT-SME', 'Small and medium sized enterprise'), ('EPLUS-ENT-LARGE', 'Large enterprise'), ('EPLUS-NGO', 'Non-governmental organisation/association/social enterprise'), ('EPLUS-FOUND', 'Foundation'), ('EPLUS-SOCIAL', 'Social partner or other representative of working life (chambers of commerce, trade union, trade association)'), ('EPLUS-RES', 'Research Institute/Centre'), ('EPLUS-YOUTH-COUNCIL', 'National Youth Council'), ('EPLUS-ENGO', 'European NGO'), ('EPLUS-NET-EU', 'EU-wide network'), ('EPLUS-YOUTH-GROUP', 'Group of young people active in youth work'), ('EPLUS-EURO-GROUP-COOP', 'European grouping of territorial cooperation'), ('EPLUS-BODY-ACCRED', 'Accreditation, _(certification or qualification body'), ('EPLUS-BODY-CONS', 'Counsellzing body'), ('EPLUS-INTER', 'International organisation under public law'), ('EPLUS-SPORT-PARTIAL', 'Organisation or association representing (parts of) the sport sector'), ('EPLUS-SPORT-FED', 'Sport federation'), ('EPLUS-SPORT-LEAGUE', 'Sport league'), ('EPLUS-SPORT-CLUB', 'Sport club'), ('OTH', 'Other')], help_text='mandatory_if_not_pic_ies', max_length=255, null=True, verbose_name='contact_type'),
        ),
        migrations.AlterField(
            model_name='partner',
            name='email',
            field=models.EmailField(blank=True, help_text='mandatory_if_not_pic_ies', max_length=254, null=True, verbose_name='email'),
        ),
        migrations.AlterField(
            model_name='partner',
            name='end_date',
            field=models.DateField(blank=True, null=True, verbose_name='partner_end_date'),
        ),
        migrations.AlterField(
            model_name='partner',
            name='phone',
            field=models.CharField(blank=True, help_text='mandatory_if_not_pic_ies', max_length=255, null=True, verbose_name='phone'),
        ),
        migrations.AlterField(
            model_name='partner',
            name='pic_code',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True, verbose_name='pic_code'),
        ),
        migrations.AlterField(
            model_name='partner',
            name='start_date',
            field=models.DateField(blank=True, null=True, verbose_name='partner_start_date'),
        ),
    ]