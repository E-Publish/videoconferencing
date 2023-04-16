# Generated by Django 4.1.7 on 2023-04-16 20:48

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ArchivesData",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=30)),
                ("code_name", models.CharField(max_length=30)),
                ("is_private", models.BooleanField()),
                ("event_date", models.DateField()),
                ("lifetime", models.DateField()),
                ("is_unremovable", models.BooleanField()),
                ("participants", models.TextField()),
                ("description", models.TextField()),
                ("handout", models.TextField()),
                ("recording", models.TextField()),
            ],
            options={
                "db_table": "conference",
            },
        ),
    ]
