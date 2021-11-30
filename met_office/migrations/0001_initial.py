# Generated by Django 3.2.9 on 2021-11-28 17:19

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='WeatherPayload',
            fields=[
                ('log_id', models.AutoField(primary_key=True, serialize=False)),
                ('process_id', models.CharField(max_length=255)),
                ('time_stamp', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('weather_time', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('country', models.CharField(choices=[('UK', 'UK'), ('England', 'England'), ('Wales', 'Wales'), ('Scotland', 'Scotland'), ('Northern_Ireland', 'Northern_Ireland'), ('England_and_Wales', 'England_and_Wales'), ('England_N', 'England_N'), ('England_S', 'England_S'), ('Scotland_N', 'Scotland_N'), ('Scotland_E', 'Scotland_E'), ('Scotland_W', 'Scotland_W'), ('England_E_and_NE', 'England_E_and_NE'), ('England_NW_and_N_Wales', 'England_NW_and_N_Wales'), ('Midlands', 'Midlands'), ('East_Anglia', 'East_Anglia'), ('England_SW_and_S_Wales', 'England_SW_and_S_Wales'), ('England_SE_and_Central_S', 'England_SE_and_Central_S')], max_length=50)),
                ('year', models.IntegerField()),
                ('month_or_season', jsonfield.fields.JSONField()),
                ('reading_type', models.CharField(choices=[('Tmin', 'Tmin'), ('Tmax', 'Tmax'), ('Tmean', 'Tmean'), ('Rainfall', 'Rainfall'), ('Sunshine', 'Sunshine'), ('Raindays1mm', 'Raindays1mm'), ('AirFrost', 'AirFrost')], max_length=100)),
                ('data_feed_type', models.CharField(choices=[('ranked', 'ranked'), ('date', 'date')], max_length=10)),
            ],
            options={
                'unique_together': {('country', 'month_or_season', 'year', 'reading_type', 'data_feed_type')},
            },
        ),
    ]