# Generated by Django 4.1 on 2022-09-13 14:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('btdyScraper', '0011_league_leagueurl'),
    ]

    operations = [
        migrations.AddField(
            model_name='series',
            name='seriesUrl',
            field=models.CharField(default='default', max_length=50),
            preserve_default=False,
        ),
    ]
