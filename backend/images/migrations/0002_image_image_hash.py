# Generated by Django 5.0 on 2025-06-01 10:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('images', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='image_hash',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ] 