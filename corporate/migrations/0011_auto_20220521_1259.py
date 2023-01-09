# Generated by Django 3.2 on 2022-05-21 03:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('corporate', '0010_auto_20220429_2342'),
    ]

    operations = [
        migrations.AddField(
            model_name='information',
            name='meta_description',
            field=models.CharField(blank=True, max_length=160, null=True, verbose_name='meta_description'),
        ),
        migrations.AlterField(
            model_name='information',
            name='category',
            field=models.IntegerField(choices=[(4, 'プレゼント'), (2, '更新'), (5, '工事'), (1, 'ニュース'), (3, 'キャンペーン')], null=True, verbose_name='category'),
        ),
        migrations.AlterField(
            model_name='information',
            name='description',
            field=models.CharField(max_length=4096, verbose_name='description'),
        ),
    ]
