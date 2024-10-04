# Generated by Django 5.1.1 on 2024-10-03 10:18

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_alter_ad_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='SearchCriteria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('keywords', models.TextField(default=None)),
                ('min_price', models.DecimalField(decimal_places=2, max_digits=7, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('max_price', models.DecimalField(decimal_places=2, max_digits=7, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('chat_id', models.ForeignKey(db_column='chat_id', on_delete=django.db.models.deletion.CASCADE, to='app.user', to_field='chat_id')),
            ],
        ),
    ]