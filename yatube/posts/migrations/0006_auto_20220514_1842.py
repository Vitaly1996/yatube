# Generated by Django 2.2.6 on 2022-05-14 15:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0005_auto_20220514_1839'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='text',
            field=models.TextField(help_text='Введите текст постаааа', verbose_name='Текст поста'),
        ),
    ]
