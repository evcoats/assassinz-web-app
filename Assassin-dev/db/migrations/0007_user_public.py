# Generated by Django 3.0.6 on 2020-06-11 21:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0006_auto_20200611_1252'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='public',
            field=models.BooleanField(default=True),
        ),
    ]