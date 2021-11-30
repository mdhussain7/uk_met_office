import re
import requests
from .constants import *
import uuid
import pytz
import datetime
from .models import WeatherPayload

def set_key_value(dump):
	try:
		if not dump:
			raise Exception('No data found')
		month_season_data = dict(zip(MONTH_OR_SEASON, dump))
		return month_season_data,'Success'
	except Exception as e:
		return '','', str(e)

def met_url_file(reading_type,data_feed,country_name):
	met_office_url = BASE_URL%(reading_type, data_feed,country_name)
	met_office_data = requests.get(met_office_url).text
	file_name = generate_unique_id('RESPONSE')+'.txt'
	with open(file_name,'w') as file_open:
		file_open.write(met_office_data)
	return file_name

def parse_met_data(file_name):
	try:
		with open(file_name,'r') as file_open:
			duplicate_check = []
			for raw_data in file_open:
				dump_data = {}
				data = re.split(" ",raw_data)
				month_year_data = []
				while "" in data:
					data.remove("")
				if len(data) == 18:
					if re.search(r'\d', data[0]):
						for i in data:
							month_year_data.append(i)
							dump_data['month_year_data'] = month_year_data
				dump_values = dump_data.get('month_year_data',None)
				if dump_values:
					month_season_data,res_str = set_key_value(dump_values)
					if month_season_data not in duplicate_check:
						duplicate_check.append(month_season_data)
			return duplicate_check
	except Exception as e:
		return []

class CustomLogger():

    def set_process_id(self,process_id):
        self.process_id = process_id

    # Creates Log handlers
    def create_log_file(self,logger_name, log_file):
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s %(levelname)s '+ self.process_id +' %(message)s')
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger

    def log_closer(self,logger):
        handlers = logger.handlers[:]
        for handler in handlers:
            handler.close()
            logger.removeHandler(handler)


def rand4Digit():
    from random import randint
    return randint(1000, 9999)


def generate_unique_id(key):
    import datetime
    dt = datetime.datetime.now()
    return key + str(dt.year) + str(dt.month) + \
        str(dt.day) + str(dt.hour) + str(dt.minute) + \
        str(dt.second) + str(dt.microsecond) + \
        str(rand4Digit()) + 'METOFFICE'

def parse_data_to_db(parse_data,requested_ip,country_name,data_feed,reading_type,file_name):
    try:
        for data in parse_data:
            year = data.get('year')
            ann = str(data.get('ann')).strip("\n")
            data['ann'] = ann
            month_or_season = data
            requested_ip = requested_ip
            process_id = generate_unique_id('UK')
            weather_time = (datetime.datetime.now()).replace(tzinfo = pytz.UTC)
            WeatherPayload.objects.create(process_id = process_id,country = country_name,\
                year = year,month_or_season = month_or_season,reading_type = reading_type,\
                data_feed_type = data_feed,weather_time = weather_time,file_name=file_name)
            SUCCESS_LOG.info("Database Updated Successfully for the file: "+ file_name +", IP Address: "+ requested_ip)
    except Exception as e:
        ERROR_LOG.error("Error while Database Update for the file: "+ file_name +"Error"+ str(e))
