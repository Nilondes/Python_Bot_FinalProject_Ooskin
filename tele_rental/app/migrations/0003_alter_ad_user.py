# Generated by Django 5.1.1 on 2024-10-02 09:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_alter_ad_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ad',
            name='user',
            field=models.ForeignKey(db_column='user', on_delete=django.db.models.deletion.CASCADE, to='app.user', to_field='username'),
        ),
    ]