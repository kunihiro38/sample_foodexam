# Generated by Django 3.2 on 2022-07-18 05:53

import corporate.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('corporate', '0015_information_eyecatch'),
    ]

    operations = [
        migrations.AlterField(
            model_name='information',
            name='eyecatch',
            field=models.ImageField(upload_to=corporate.models._info_eyecatch_upload_to, verbose_name='eyecatch'),
        ),
    ]
