# Generated by Django 3.0.4 on 2020-04-25 01:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cloudships", "0001_init"),
    ]

    operations = [
        migrations.AlterField(
            model_name="gamesetup",
            name="orientation",
            field=models.TextField(
                choices=[("horizontal", "Horizontal"), ("vertical", "Vertical")], max_length=15
            ),
        ),
    ]
