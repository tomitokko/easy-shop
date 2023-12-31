# Generated by Django 4.1 on 2023-02-01 20:05

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0018_delete_cart'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.CharField(default=uuid.uuid4, max_length=1000, primary_key=True, serialize=False)),
                ('product_id', models.CharField(max_length=10000)),
                ('user_username', models.CharField(max_length=10000)),
                ('quantity', models.IntegerField(default=0)),
            ],
        ),
    ]
