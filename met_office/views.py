# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.views.generic import View
from django.http.response import JsonResponse
import logging
import os
# from djcelery.models import PeriodicTask
import json
import datetime
from django.core import serializers
# from .tasks import json_adaptor_process
from .models import WeatherPayload
import requests
from .utils import *
from .constants import *
from collections import OrderedDict

# ----------- POST API User Input Start -------------
# reading_type can have either of the following Tmin', 'Tmax', 'Tmean', 'Rainfall', 'Sunshine','Raindays1mm','AirFrost'
# data_feed can have 'date','ranked'
# country_name can have either of the following 'UK', 'England', 'Wales', 'Scotland','Northern_Ireland','England_and_Wales','England_N','England_S','Scotland_N','Scotland_E','Scotland_W','England_E_and_NE','England_NW_and_N_Wales','Midlands','East_Anglia','England_SW_and_S_Wales','England_SE_and_Central_S'
# ----------- POST User Input End --------------


#------------- GET API User Input Start --------------
# reading_type can have either of the following Tmin', 'Tmax', 'Tmean', 'Rainfall', 'Sunshine','Raindays1mm','AirFrost'
# data_feed can have 'date','ranked'
# country can have either of the following 'UK', 'England', 'Wales', 'Scotland','Northern_Ireland','England_and_Wales','England_N','England_S','Scotland_N','Scotland_E','Scotland_W','England_E_and_NE','England_NW_and_N_Wales','Midlands','East_Anglia','England_SW_and_S_Wales','England_SE_and_Central_S'
# if you know the process_id you can fetch from it
# if you knwow the file_name 
#------------ GET API User Input End ----------------


# Create your views here.
class BaseView(View):

    def __init__(self):
        self.response = {}
        self.response['res_code'] = '1'
        self.response['res_str'] = 'Processed Successfully'
        self.response['res_data'] = {}

class WeatherDataParse(BaseView):

    def get(self,request):
        try:
            params = request.GET

            pid = str(uuid.uuid4().hex)
            import pdb;pdb.set_trace()
            custom_process = CustomLogger()
            custom_process.set_process_id(pid)
            SUCCESS_LOG = custom_process.create_log_file(SUCCESS_NAME,SUCCESS_FILE)
            ERROR_LOG = custom_process.create_log_file(ERROR_NAME,ERROR_FILE)

            page = params.get('page', 1)
            per_page = params.get('per_page', 10)
            process_id = params.get('process_id',None)
            year = params.get('year',None)
            country = params.get('country', None)
            reading_type = params.get('reading_type',None)
            file_name = params.get('file_name',None)
            query_params = {
                            "from_date": params.get("from_date"),
                            "to_date": params.get("to_date")
                            }
            if process_id:
                query_params['process_id'] = process_id
            if year:
                query_params['year'] = year
            if country:
                query_params['country'] = country
            if reading_type:
                query_params['reading_type'] = reading_type
            if file_name:
                query_params['file_name'] = file_name
            payloads_log_paginated_set, payload_log_info = WeatherPayload.objects.list_payload(page = page,
                                per_page = per_page,query_params = query_params)
            total_pay_loads = payloads_log_paginated_set.total_objects
            if total_pay_loads == 0:
                raise Exception('No data found for the details')
            # payload_info = list(payload_log_info)
            payload_info_list = []
            for query in payload_log_info:
                payload_info_list.append(query.month_or_season)
            self.response['res_data']['results'] = payload_info_list
            self.response['res_data']['count'] = total_pay_loads
            self.response['res_data']['has_next'] = payloads_log_paginated_set.has_next
            SUCCESS_LOG.info("Data Fetched Successfully, Status: 200")
            return JsonResponse(data =self.response, status=201)
        except Exception as e:
            self.response['res_str'] = GENERIC_ERROR
            ERROR_LOG.error("Error while Fetching data: "+ str(e) +", Status: 400")
            return JsonResponse(data=self.response,safe=False,  status=400)

    def post(self,request):
        try:
            params = request.POST
            import pdb;pdb.set_trace()
            pid = str(uuid.uuid4().hex)
            custom_process = CustomLogger()
            custom_process.set_process_id(pid)

            SUCCESS_LOG = custom_process.create_log_file(SUCCESS_NAME,SUCCESS_FILE)
            ERROR_LOG = custom_process.create_log_file(ERROR_NAME,ERROR_FILE)

            url = "https://ifconfig.co/ip"
            ip_address = requests.get(url)
            batch_size = 20
            reading_type = params.get('reading_type')
            data_feed = params.get('data_feed')
            country_name = params.get('country_name')
            file_name = met_url_file(reading_type,data_feed,country_name)
            parsed_data = parse_met_data(file_name)
            requested_ip = str(ip_address._content).strip("b'\\n'")
            if not parsed_data:
                raise Exception('No data found in parsing')
            for chunks_data in range(0,len(parsed_data),batch_size):
                parse_data_to_db(parsed_data[chunks_data:chunks_data+batch_size],\
                    requested_ip,country_name,data_feed,reading_type,file_name)
            self.response['res_str'] = "Parse File has been initiated, Data will be synced shortly"
            self.response['res_data']['requester_ip'] = requested_ip
            SUCCESS_LOG.info("File Name: "+ file_name +", IP Address: "+ requested_ip +", FIle Parsed Successfully, Status: 200")
            os.remove(file_name)
            return JsonResponse(data=self.response,safe=False,  status=201)
        except Exception as e:
            self.response['res_str'] = GENERIC_ERROR
            ERROR_LOG.error("File Name: "+ file_name +", with Error: "+ str(e) +"Status: 400")
            return JsonResponse(data=self.response,safe=False,  status=400)

