# Generated by Django 2.2 on 2021-09-25 07:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jrfoodadv', '0005_auto_20210814_1627'),
    ]

    operations = [
        migrations.CreateModel(
            name='TimeLeft',
            fields=[
                ('user_id', models.IntegerField(primary_key=True, serialize=False, verbose_name='user_id')),
                ('time_left_at', models.DateTimeField(verbose_name='time_left_at')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created_at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated_at')),
            ],
        ),
    ]