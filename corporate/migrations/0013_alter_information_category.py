# Generated by Django 3.2 on 2022-06-15 13:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('corporate', '0012_auto_20220522_0959'),
    ]

    operations = [
        migrations.AlterField(
            model_name='information',
            name='category',
            field=models.IntegerField(choices=[(1, 'ニュース'), (2, '更新'), (3, 'キャンペーン'), (4, 'プレゼント'), (5, '工事'), (6, 'コラム')], null=True, verbose_name='category'),
        ),
    ]