# Generated by Django 2.2 on 2021-10-10 04:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('corporate', '0008_information'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usercourse',
            name='payment_course',
            field=models.IntegerField(choices=[(0, 'コース選択をお願いします'), (1, '初級食品表示診断士コース'), (2, '中級食品表示診断士コース')], default=0, verbose_name='payment_course'),
        ),
    ]
