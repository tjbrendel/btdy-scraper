# Generated by Django 4.0.4 on 2022-05-27 23:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('btdyScraper', '0005_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='points',
            name='penalty',
            field=models.IntegerField(default=0),
        ),
    ]
