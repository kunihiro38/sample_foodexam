# Generated by Django 3.2 on 2022-10-11 13:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('corporate', '0016_alter_information_eyecatch'),
    ]

    operations = [
        migrations.AddField(
            model_name='usercourse',
            name='foodadv_expired_at',
            field=models.DateTimeField(null=True, verbose_name='foodadv_expired_at'),
        ),
        migrations.AddField(
            model_name='usercourse',
            name='foodadv_paid_at',
            field=models.DateTimeField(null=True, verbose_name='foodadv_paid_at'),
        ),
        migrations.AddField(
            model_name='usercourse',
            name='foodadv_payment_course',
            field=models.IntegerField(choices=[(0, 'コース選択をお願いします'), (1, '初級食品表示診断士コース'), (2, '中級食品表示診断士コース')], default=0, verbose_name='foodadv_payment_course'),
        ),
    ]
