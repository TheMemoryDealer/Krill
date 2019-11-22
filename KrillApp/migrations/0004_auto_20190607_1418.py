# Generated by Django 2.1.3 on 2019-06-07 13:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('KrillApp', '0003_krill_unique_krill_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='krill',
            name='bounding_box_num',
            field=models.CharField(max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='krill',
            name='length',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='krill',
            name='unique_krill_id',
            field=models.CharField(max_length=50, unique=True),
        ),
    ]
