# Generated by Django 2.2 on 2022-04-18 13:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jrfoodadv', '0006_timeleft'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='jrfoodlabelingadvisequestion',
            name='child_question',
        ),
        migrations.RemoveField(
            model_name='jrfoodlabelingadvisequestion',
            name='parent_question',
        ),
        migrations.AlterField(
            model_name='jrfoodlabelingadvisequestion',
            name='choice_d',
            field=models.CharField(blank=True, max_length=126, null=True, verbose_name='choice_d'),
        ),
    ]
