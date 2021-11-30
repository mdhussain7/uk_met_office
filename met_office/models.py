# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
# import jsonfield
from jsonfield import JSONField
# from django.contrib.postgres import fields
# from django.contrib.postgres.fields.jsonb import JSONField
import uuid
import datetime
import json
from django.db.models import Count
from .pagination import QuerySetPagination
# from django_mysql.models import JSONField
import pytz

class WeatherPayloadManager(models.Manager):
    def list_payload(self,page, per_page,query_params={}):
        query_params = {k: v for k, v in query_params.items() if v}
        date_format = "%Y-%m-%d %H:%M:%S"
        if query_params.get("from_date"):
            from_date_string = "{} 00:00:00".format(query_params.get("from_date"))
            query_params["weather_time__gte"] = datetime.datetime.strptime(from_date_string, date_format)
            query_params.pop("from_date")

        if query_params.get("to_date"):
            to_date_string = "{} 23:59:59".format(query_params.get("to_date"))
            query_params["weather_time__lte"] = datetime.datetime.strptime(to_date_string, date_format)
            query_params.pop("to_date")

        payload_log_set = self.filter(**query_params).\
                                    order_by('-weather_time')
        payload_log_paginated_set = QuerySetPagination(payload_log_set,
                                                     int(per_page),int(page))
        return payload_log_paginated_set, payload_log_set

# Create your models here.
class WeatherPayload(models.Model):
    COUNTRIES = (
    				('UK','UK'), 
    				('England','England'),
    				('Wales','Wales'),
    				('Scotland','Scotland'),
    				('Northern_Ireland','Northern_Ireland'),
    				('England_and_Wales','England_and_Wales'),
    				('England_N','England_N'),
    				('England_S','England_S'),
    				('Scotland_N','Scotland_N'),
    				('Scotland_E','Scotland_E'),
    				('Scotland_W','Scotland_W'),
    				('England_E_and_NE','England_E_and_NE'),
    				('England_NW_and_N_Wales','England_NW_and_N_Wales'),
    				('Midlands','Midlands'),('East_Anglia','East_Anglia'),
    				('England_SW_and_S_Wales','England_SW_and_S_Wales'),
    				('England_SE_and_Central_S','England_SE_and_Central_S')
    			)

    READING_TYPES = (
    					('Tmin','Tmin'),
    					('Tmax','Tmax'),
    					('Tmean','Tmean'),
    					('Rainfall','Rainfall'),
    					('Sunshine','Sunshine'),
    					('Raindays1mm','Raindays1mm'),
    					('AirFrost','AirFrost')
    				) 

    DATA_FEED = (
    				('ranked','ranked'),
    				('date','date')
    			)

    log_id = models.AutoField(primary_key=True)
    process_id = models.CharField(max_length=255)
    time_stamp = models.DateTimeField(auto_now_add=True, db_index=True)
    weather_time = models.DateTimeField(db_index=True,null=True, blank=True)
    country = models.CharField(max_length=50,choices=COUNTRIES)
    year = models.IntegerField()
    month_or_season = JSONField()
    reading_type = models.CharField(max_length=100,choices=READING_TYPES)
    data_feed_type =  models.CharField(max_length=10, choices=DATA_FEED)
    file_name = models.CharField(max_length=20)
    objects = WeatherPayloadManager()
    class Meta:
        unique_together = (("country", "month_or_season", "year", "reading_type","data_feed_type"))

    def __unicode__(self):
        return str(self.month_or_season)

    def serialize(self):
        serialized_data = {}
        serialized_data['process_id'] = self.process_id
        serialized_data['pk'] = self.log_id
        serialized_data['country'] = self.country
        serialized_data['month_or_season'] = json.loads(self.month_or_season)
        serialized_data['year'] = self.year
        serialized_data['reading_type'] = self.reading_type
        serialized_data['data_feed_type'] = self.data_feed_type
        serialized_data['file_name'] = self.file_name
        return serialized_data


