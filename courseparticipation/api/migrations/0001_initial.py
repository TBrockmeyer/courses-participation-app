# Generated by Django 3.0.7 on 2020-10-18 05:48

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Course',
            fields=[
                ('course_id', models.AutoField(primary_key=True, serialize=False, unique=True)),
                ('course_title', models.CharField(blank=True, default='', max_length=100)),
            ],
        ),
    ]
