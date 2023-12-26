# Generated by Django 4.1 on 2023-01-13 12:44

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0005_alter_store_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='store',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False),
        ),
    ]