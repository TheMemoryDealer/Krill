# Generated by Django 3.0.2 on 2020-01-22 15:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('KrillApp', '0011_krill_position'),
    ]

    operations = [
        migrations.AddField(
            model_name='krill',
            name='altr_view',
            field=models.TextField(default=''),
        ),
    ]
