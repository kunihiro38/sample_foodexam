# Generated by Django 2.2 on 2021-08-14 07:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jrfoodadv', '0004_auto_20210731_1622'),
    ]

    operations = [
        migrations.RenameField(
            model_name='jrfoodlabelingadvisequestion',
            old_name='create_at',
            new_name='created_at',
        ),
    ]
