# Generated by Django 5.1.7 on 2025-03-15 01:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='certificate',
            name='ipfs_hash',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
    ]
