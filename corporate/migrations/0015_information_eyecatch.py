# Generated by Django 3.2 on 2022-07-18 02:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('corporate', '0014_auto_20220706_2308'),
    ]

    operations = [
        migrations.AddField(
            model_name='information',
            name='eyecatch',
            field=models.ImageField(default='images/info/column.jpg', upload_to='images/info/column/', verbose_name='eyecatch'),
        ),
    ]
