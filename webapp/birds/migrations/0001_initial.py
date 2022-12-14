# Generated by Django 4.0.6 on 2022-07-23 10:36

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Bird',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bird_id', models.IntegerField()),
                ('bird_name', models.CharField(max_length=200)),
                ('recorded_datetime', models.DateTimeField()),
                ('probability', models.FloatField()),
            ],
        ),
    ]
