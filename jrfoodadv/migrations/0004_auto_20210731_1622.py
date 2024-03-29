# Generated by Django 2.2 on 2021-07-31 07:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jrfoodadv', '0003_auto_20210717_1332'),
    ]

    operations = [
        migrations.AddField(
            model_name='record',
            name='saved_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='saved_at'),
        ),
        migrations.AlterField(
            model_name='record',
            name='current_answer',
            field=models.IntegerField(choices=[(0, '未実施'), (1, '未解答'), (2, '不正解'), (3, '正解')], default=0, verbose_name='current_answer'),
        ),
        migrations.AlterField(
            model_name='record',
            name='current_choice',
            field=models.CharField(blank=True, max_length=126, null=True, verbose_name='current_choice'),
        ),
        migrations.AlterField(
            model_name='record',
            name='fifth_answer',
            field=models.IntegerField(blank=True, choices=[(0, '未実施'), (1, '未解答'), (2, '不正解'), (3, '正解')], default=0, null=True, verbose_name='fifth_answer'),
        ),
        migrations.AlterField(
            model_name='record',
            name='first_answer',
            field=models.IntegerField(choices=[(0, '未実施'), (1, '未解答'), (2, '不正解'), (3, '正解')], default=0, null=True, verbose_name='first_answer'),
        ),
        migrations.AlterField(
            model_name='record',
            name='fourth_answer',
            field=models.IntegerField(blank=True, choices=[(0, '未実施'), (1, '未解答'), (2, '不正解'), (3, '正解')], default=0, null=True, verbose_name='fourth_answer'),
        ),
        migrations.AlterField(
            model_name='record',
            name='memo',
            field=models.CharField(blank=True, default='', max_length=512, null=True, verbose_name='memo'),
        ),
        migrations.AlterField(
            model_name='record',
            name='second_answer',
            field=models.IntegerField(blank=True, choices=[(0, '未実施'), (1, '未解答'), (2, '不正解'), (3, '正解')], default=0, null=True, verbose_name='second_answer'),
        ),
        migrations.AlterField(
            model_name='record',
            name='third_answer',
            field=models.IntegerField(blank=True, choices=[(0, '未実施'), (1, '未解答'), (2, '不正解'), (3, '正解')], default=0, null=True, verbose_name='third_answer'),
        ),
    ]
