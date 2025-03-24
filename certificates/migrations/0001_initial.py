# Generated by Django 5.1.7 on 2025-03-15 01:18

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Certificate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_name', models.CharField(max_length=200)),
                ('course', models.CharField(max_length=200)),
                ('institution', models.CharField(max_length=200)),
                ('issue_date', models.DateTimeField()),
                ('cert_hash', models.CharField(max_length=66, unique=True)),
                ('ipfs_hash', models.CharField(max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
