# Generated by Django 2.0 on 2018-10-20 01:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0002_auto_20181019_2044'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='billet',
            name='prix_brut',
        ),
        migrations.AddField(
            model_name='train',
            name='prix_brut',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
