# Generated by Django 3.0.2 on 2020-01-22 16:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('KrillApp', '0012_krill_altr_view'),
    ]

    operations = [
        migrations.AddField(
            model_name='krill',
            name='altr_height',
            field=models.CharField(default='', max_length=50),
        ),
        migrations.AddField(
            model_name='krill',
            name='altr_width',
            field=models.CharField(default='', max_length=50),
        ),
        migrations.AddField(
            model_name='krill',
            name='altr_x',
            field=models.CharField(default='', max_length=50),
        ),
        migrations.AddField(
            model_name='krill',
            name='altr_y',
            field=models.CharField(default='', max_length=50),
        ),
    ]
