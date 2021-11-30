import logging
import os

MONTH_OR_SEASON = ['year','jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec','win','spr','sum','aut','ann']
COUNTRIES = ['UK', 'England', 'Wales', 'Scotland','Northern_Ireland','England_and_Wales','England_N','England_S','Scotland_N','Scotland_E','Scotland_W','England_E_and_NE','England_NW_and_N_Wales','Midlands','East_Anglia','England_SW_and_S_Wales','England_SE_and_Central_S']
READING_TYPES = ['Tmin', 'Tmax', 'Tmean', 'Rainfall', 'Sunshine','Raindays1mm','AirFrost']
DATA_FEED = ['ranked', 'date']
BASE_URL = 'https://www.metoffice.gov.uk/pub/data/weather/uk/climate/datasets/%s/%s/%s.txt'

#Log Details
ERROR_NAME = 'Error_Log'
LOG_PATH = 'logs'
ERROR_FILE = 'debug.log'
SUCCESS_NAME = 'Success_Log'
SUCCESS_FILE = 'debug.log'
ERROR_LOG = logging.getLogger(ERROR_NAME)
SUCCESS_LOG = logging.getLogger(SUCCESS_NAME)
GENERIC_ERROR='"Something Went Wrong, Please try again later"'