# Generated by Django 2.2 on 2021-09-03 00:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('corporate', '0005_delete_information'),
    ]

    operations = [
        migrations.CreateModel(
            name='Information',
            fields=[
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('description', models.CharField(max_length=1024, verbose_name='description')),
                ('contributor', models.IntegerField(primary_key=True, serialize=False, verbose_name='contributor')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created_at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated_at')),
            ],
        ),
    ]
