# Generated by Django 2.2.16 on 2022-05-27 15:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0013_auto_20220525_2221'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='text',
            field=models.TextField(help_text='Введите комментарий к посту', verbose_name='Комментарий к посту'),
        ),
    ]
