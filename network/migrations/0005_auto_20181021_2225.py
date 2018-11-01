# Generated by Django 2.0 on 2018-10-21 22:25

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('network', '0004_auto_20181020_0204'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='client',
            name='mail',
        ),
        migrations.RemoveField(
            model_name='client',
            name='nom',
        ),
        migrations.AddField(
            model_name='client',
            name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]