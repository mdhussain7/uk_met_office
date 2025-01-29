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

import concurrent.futures
from requests_kerberos import HTTPKerberosAuth, DISABLED
from pymongo.operations import UpdateOne
from core.utils.database import tai_role_sync_col
from datetime import datetime
from retrying import retry
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class TaiDataSynch(object):
    BASE_ENDPOINT = {
        "dev": "http://taidss.webfarm.ms.com/web/1/services/query",
        "qa": "http://taidss.webfarm-qa.ms.com/web/1/services/query",
        "uat": "http://taidss.webfarm.ms.com/web/1/services/query",
        "prod": "http://taidss.webfarm.ms.com/web/1/services/query"
    }

    def __init__(self, env: str = "prod"):
        self.session = requests.Session()

        # Set up retries and connection pooling
        retry_strategy = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=100, pool_maxsize=100, pool_block=True)
        self.session.mount("http://", adapter)
        self.session.auth = HTTPKerberosAuth(mutual_authentication=DISABLED)

        self.env = env
        self.dataset = "system"
        self.base_url = self.BASE_ENDPOINT[self.env]
        self.columns = "system.system, system.eon_id, system.primary_technology_owner, " \
                       "system.technology_owner, system.primary_business_owner, system.business_owner"
        self.user_dataset = "user_roles"
        self.filter = "system.system"
        self.user_column = "user.user"
        self.url = f"{self.base_url}/{self.dataset}?c={self.columns}"

    def get_user_response(self, eon_id):
        user_url = f"{self.base_url}/{self.user_dataset}/?f={self.filter}={eon_id}&c={self.user_column}"
        try:
            user_response = self.session.get(user_url, timeout=60)
            user_response.raise_for_status()
            user_data = user_response.json().get('data', [])
            return list(set(user['user.user'] for user in user_data))
        except requests.exceptions.RequestException as e:
            print(f"Error fetching users for EON ID {eon_id}: {e}")
            return []

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
            response = self.session.get(self.url, timeout=60)
            response.raise_for_status()
            data = response.json().get("data", [])
            print(f"Number of Records: {response.json().get('numberOfRecords')}")
            if not data:
                raise Exception('No data received from TAI')

            # Fetch existing EON IDs from the database in one query
            eonid_in_db = set(record["eon_id"] for record in tai_role_sync_col.find({}, {"eon_id": 1, "_id": 0}))

            values_to_update = []
            values_to_insert = []

            # Create a ThreadPoolExecutor to process the user responses concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:  # Optimized thread pool size
                # Prepare a list of futures for the get_user_response function
                futures = {eon_id: executor.submit(self.get_user_response, eon_id) for eon_id in [record["system.eon_id"] for record in data]}

                # Process each record and user response in parallel
                for record in data:
                    eon_id = record["system.eon_id"]
                    users = futures[eon_id].result()

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






          ==========================================================================================================================================

from requests_kerberos import HTTPKerberosAuth, DISABLED
from pymongo.operations import UpdateOne
from core.utils.database import tai_role_sync_col
from core.utils.exceptions import ConfigError
from core.utils.config import paw_config
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
        self.session = requests.Session()
        self.session.auth = HTTPKerberosAuth(mutual_authentication=DISABLED)
        self.base_url = self.BASE_ENDPOINT[self.env]
        self.columns = "system.system, system.eon_id, system.primary_technology_owner, " \
                       "system.technology_owner, system.primary_business_owner, system.business_owner"
        self.user_dataset = "user_roles"
        self.filter = "system.system"
        self.user_column = "user.user"
        self.url = f"{self.base_url}/{self.dataset}?c={self.columns}"

    def get_user_response(self, eon_id):
        user_url = f"{self.base_url}/{self.user_dataset}/?f={self.filter}={eon_id}&c={self.user_column}"
        try:
            user_response = self.session.get(user_url, timeout=60)
            user_response.raise_for_status()
            user_data = user_response.json().get('data', [])
            return list(set(user['user.user'] for user in user_data))
        except requests.exceptions.RequestException as e:
            print(f"Error fetching users for EON ID {eon_id}: {e}")
            return []

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
            response = self.session.get(self.url, timeout=60)
            response.raise_for_status()
            data = response.json().get("data", [])
            print(f"Number of Records: {response.json().get('numberOfRecords')}")
            if not data:
                raise Exception('No data received from TAI')

            # Fetch existing EON IDs from the database
            eonid_in_db = list(tai_role_sync_col.find({}, {"eon_id": 1, "_id": 0}))
            eonid_db = [record["eon_id"] for record in eonid_in_db]

            # Extract EON IDs from the TAI API response
            eonid_in_tai = [record["system.eon_id"] for record in data]

            values_to_update = []
            if set(eonid_in_tai).intersection(set(eonid_db)):
                for record in data:
                    users = self.get_user_response(record['system.eon_id'])
                    new_values_to_update = {
                        "technology_owner": self.parse_owner_field(record["system.primary_technology_owner"], record["system.technology_owner"]),
                        "business_owner": self.parse_owner_field(record["system.primary_business_owner"], record["system.business_owner"]),
                        "users": users,
                        "updated_at": datetime.now()
                    }

                    values_to_update.append(UpdateOne(
                        {"eon_id": record["system.eon_id"]},
                        {"$set": new_values_to_update},
                        upsert=True
                    ))

                if values_to_update:
                    tai_role_sync_col.bulk_write(values_to_update)
            else:
                # Insert operations for new records
                eonid_not_in_db = set(eonid_in_tai) - set(eonid_db)
                values_to_insert = []
                for record in data:
                    if record['system.eon_id'] in eonid_not_in_db:
                        users = self.get_user_response(record['system.eon_id'])
                        values_to_insert.append({
                            "eon_id": record["system.eon_id"],
                            "technology_owner": self.parse_owner_field(record["system.primary_technology_owner"], record["system.technology_owner"]),
                            "business_owner": self.parse_owner_field(record["system.primary_business_owner"], record["system.business_owner"]),
                            "users": users,
                            "created_at": datetime.now(),
                            "updated_at": datetime.now()
                        })

                if values_to_insert:
                    tai_role_sync_col.insert_many(values_to_insert)

        except Exception as e:
            print(f"Exception: {str(e)}")
            self.handle_error(e)

    def parse_owner_field(self, primary_owner, additional_owners):
        owners = [primary_owner]
        if additional_owners:
            owners.extend(str(additional_owners).split(","))
        return list(set(owners))

==============================================================================================================
import aiohttp
import asyncio
from requests_kerberos import HTTPKerberosAuth, DISABLED
from pymongo.operations import UpdateOne
from core.utils.database import tai_role_sync_col
from datetime import datetime
from retrying import retry
import time

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
        self.base_url = self.BASE_ENDPOINT[self.env]
        self.columns = "system.system, system.eon_id, system.primary_technology_owner, " \
                       "system.technology_owner, system.primary_business_owner, system.business_owner"
        self.user_dataset = "user_roles"
        self.filter = "system.system"
        self.user_column = "user.user"
        self.url = f"{self.base_url}/{self.dataset}?c={self.columns}"

    async def get_user_response(self, session, eon_id):
        user_url = f"{self.base_url}/{self.user_dataset}/?f={self.filter}={eon_id}&c={self.user_column}"
        try:
            async with session.get(user_url, timeout=60) as user_response:
                user_response.raise_for_status()
                user_data = await user_response.json()
                return list(set(user['user.user'] for user in user_data.get('data', [])))
        except Exception as e:
            print(f"Error fetching users for EON ID {eon_id}: {e}")
            return []

    async def fetch_tai_data(self, session):
        try:
            async with session.get(self.url, timeout=60) as response:
                response.raise_for_status()
                data = await response.json()
                print(f"Number of Records: {data.get('numberOfRecords')}")
                return data.get("data", [])
        except Exception as e:
            print(f"Error fetching TAI data: {e}")
            return []

    def handle_error(self, error):
        if isinstance(error, requests.exceptions.RequestException):
            print('Retrying after a short delay.....')
            time.sleep(5)
        else:
            print('Critical error occurred, aborting the sync')

    @retry(stop_max_attempt_number=5, wait_fixed=7000)
    async def synch_tai_data(self):
        async with aiohttp.ClientSession(auth=HTTPKerberosAuth(mutual_authentication=DISABLED)) as session:
            try:
                data = await self.fetch_tai_data(session)
                if not data:
                    raise Exception('No data received from TAI')

                # Fetch existing EON IDs from the database
                eonid_in_db = list(tai_role_sync_col.find({}, {"eon_id": 1, "_id": 0}))
                eonid_db = [record["eon_id"] for record in eonid_in_db]

                # Extract EON IDs from the TAI API response
                eonid_in_tai = [record["system.eon_id"] for record in data]

                values_to_update = []
                if set(eonid_in_tai).intersection(set(eonid_db)):
                    tasks = []
                    for record in data:
                        tasks.append(self.process_record(session, record, values_to_update))

                    await asyncio.gather(*tasks)

                # Perform bulk write operation
                if values_to_update:
                    tai_role_sync_col.bulk_write(values_to_update)

                # Handle insertions for new records
                eonid_not_in_db = set(eonid_in_tai) - set(eonid_db)
                values_to_insert = []
                for record in data:
                    if record['system.eon_id'] in eonid_not_in_db:
                        users = await self.get_user_response(session, record['system.eon_id'])
                        values_to_insert.append({
                            "eon_id": record["system.eon_id"],
                            "technology_owner": self.parse_owner_field(record["system.primary_technology_owner"], record["system.technology_owner"]),
                            "business_owner": self.parse_owner_field(record["system.primary_business_owner"], record["system.business_owner"]),
                            "users": users,
                            "created_at": datetime.now(),
                            "updated_at": datetime.now()
                        })

                if values_to_insert:
                    tai_role_sync_col.insert_many(values_to_insert)

            except Exception as e:
                print(f"Exception: {str(e)}")
                self.handle_error(e)

    async def process_record(self, session, record, values_to_update):
        users = await self.get_user_response(session, record['system.eon_id'])
        new_values_to_update = {
            "technology_owner": self.parse_owner_field(record["system.primary_technology_owner"], record["system.technology_owner"]),
            "business_owner": self.parse_owner_field(record["system.primary_business_owner"], record["system.business_owner"]),
            "users": users,
            "updated_at": datetime.now()
        }
        values_to_update.append(UpdateOne(
            {"eon_id": record["system.eon_id"]},
            {"$set": new_values_to_update},
            upsert=True
        ))

    def parse_owner_field(self, primary_owner, additional_owners):
        owners = [primary_owner]
        if additional_owners:
            owners.extend(str(additional_owners).split(","))
        return list(set(owners))

# To run the asynchronous process
async def run_sync():
    tai_sync = TaiDataSynch(env="prod")
    await tai_sync.synch_tai_data()

# Run the async function using asyncio event loop
if __name__ == '__main__':
    asyncio.run(run_sync())

</pre>
