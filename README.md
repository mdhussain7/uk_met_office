<pre>
# uk_met_office<br>
This is a Python - django based project.<br>
Please setup a virtual enviroment for the project.<br>
step-1: command: python3 -m venv py3env<br>
step-2: command: source ./py3env/bin/activate #activate for deactivate use command: deactivate<br>
step-3: clone the project using the link https://github.com/mdhussain7/uk_met_office.git<br>
step-4: pip3 install -r requirements.txt<br>
step-5: After the successfull installation, <br> please goto the **py3env** and check for the location mentioned below <br>
          ----    lib/python/site-packages/jsonfield/encoder.py<br>
          ----    search for **from django.utils import six, timezone** <br>
          ----    change it to as mentioned below,
                --   from django.utils import timezone
                --   try:
                         from django.utils import six
                     except:
                         import six

step-6: run command: python3 manage.py makemigrations
step-7: run command: python3 manage.py migrate
step-8: run command: python3 manage.py runserver 0:8000

Go to Postman application

Create a request in postman
BASE URL: http://127.0.0.1:8000/weather-parse/

 #----------- POST API User Input Start ------------- #<br>
 reading_type can have either of the following Tmin', 'Tmax', 'Tmean', 'Rainfall', 'Sunshine','Raindays1mm','AirFrost'<br>
 data_feed can have 'date','ranked'<br>
 country_name can have either of the following 'UK', 'England', 'Wales', 'Scotland','Northern_Ireland','England_and_Wales','England_N','England_S','Scotland_N','Scotland_E','Scotland_W','England_E_and_NE','England_NW_and_N_Wales','Midlands','East_Anglia','England_SW_and_S_Wales','England_SE_and_Central_S' <br>
 #----------- POST User Input End --------------#


#------------- GET API User Input Start -------------- #<br>
 reading_type can have either of the following Tmin', 'Tmax', 'Tmean', 'Rainfall', 'Sunshine','Raindays1mm','AirFrost' <br>
 data_feed can have 'date','ranked'<br>
 country can have either of the following 'UK', 'England', 'Wales', 'Scotland','Northern_Ireland','England_and_Wales','England_N','England_S','Scotland_N','Scotland_E','Scotland_W','England_E_and_NE','England_NW_and_N_Wales','Midlands','East_Anglia','England_SW_and_S_Wales','England_SE_and_Central_S' <br>
 if you know the process_id you can fetch from it <br>
 if you knwow the file_name <br>
#------------ GET API User Input End ----------------#

import grequests
from requests_kerberos import HTTPKerberosAuth, DISABLED
from pymongo.operations import UpdateOne
from core.utils.database import tai_role_sync_col
from datetime import datetime
from retrying import retry
import time
import requests

class TaiDataSynch(object):

    BASE_ENDPOINT = {
        "dev": "http://taidss.webfarm.ms.com/web/1/services/query",
        "qa": "http://taidss.webfarm-qa.ms.com/web/1/services/query",
        "uat": "http://taidss.webfarm.ms.com/web/1/services/query",
        "prod": "http://taidss.webfarm.ms.com/web/1/services/query"
    }

    def __init__(self, env: str = "prod"):
        self.headers = {}
        self.env = env
        self.dataset = "system"
        session = requests.Session()
        session.auth = HTTPKerberosAuth(mutual_authentication=DISABLED)
        self.base_url = self.BASE_ENDPOINT[self.env]
        self.columns = "system.system, system.eon_id, system.primary_technology_owner, " \
                       "system.technology_owner, system.primary_business_owner, system.business_owner"
        self.user_dataset = "user_roles"
        self.filter = "system.system"
        self.user_column = "user.user"
        self.url = f"{self.base_url}/{self.dataset}?c={self.columns}"

    def get_user_response(self, eon_id):
        """Return a grequest object for async fetching users for a specific EON ID."""
        user_url = f"{self.base_url}/{self.user_dataset}/?f={self.filter}={eon_id}&c={self.user_column}"
        try:
            return grequests.get(user_url, auth=HTTPKerberosAuth(principal=""), timeout=60)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching users for EON ID {eon_id}: {e}")
            return None

    def handle_error(self, error):
        if isinstance(error, requests.exceptions.RequestException):
            print('Retrying after a short delay.....')
            time.sleep(5)
        else:
            print('Critical error occurred, aborting the sync')

    @retry(stop_max_attempt_number=5, wait_fixed=7000)
    def synch_tai_data(self):
        try:
            print(f"TAI Request API: {self.url}")
            response = requests.get(self.url, auth=HTTPKerberosAuth(principal=""), timeout=60)
            response.raise_for_status()
            data = response.json().get("data", [])
            print(f"Number of Records: {response.json().get('numberOfRecords')}")
            if not data:
                raise Exception('No data received from TAI')

            # Fetch existing EON IDs from the database in one query
            eonid_in_db = set(record["eon_id"] for record in tai_role_sync_col.find({}, {"eon_id": 1, "_id": 0}))

            values_to_update = []
            values_to_insert = []

            # Create the list of requests for fetching user data concurrently
            user_requests = [self.get_user_response(record["system.eon_id"]) for record in data]

            # Use grequests to send requests concurrently and process responses
            responses = grequests.map(user_requests)

            # Process each record and user response concurrently
            for record, response in zip(data, responses):
                eon_id = record["system.eon_id"]
                if response:
                    user_data = response.json().get('data', [])
                    users = list(set(user['user.user'] for user in user_data))
                else:
                    users = []

                technology_owner = list(set([record["system.primary_technology_owner"]] + 
                                           str(record.get("system.technology_owner", "")).split(",")))
                business_owner = list(set([record["system.primary_business_owner"]] + 
                                          str(record.get("system.business_owner", "")).split(",")))

                new_values = {
                    "eon_id": eon_id,
                    "technology_owner": technology_owner,
                    "business_owner": business_owner,
                    "users": users,
                    "updated_at": datetime.now()
                }

                if eon_id in eonid_in_db:
                    # Prepare for update
                    values_to_update.append(UpdateOne({"eon_id": eon_id}, {"$set": new_values}, upsert=True))
                else:
                    # Prepare for insert
                    values_to_insert.append(new_values)

            # Perform bulk operations if needed
            if values_to_update:
                tai_role_sync_col.bulk_write(values_to_update)
            if values_to_insert:
                tai_role_sync_col.insert_many(values_to_insert)

        except Exception as e:
            print('Exception: ', str(e))
            self.handle_error(e)

</pre>
