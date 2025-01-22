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

from pymongo import UpdateOne
from requests_kerberos import HTTPKerberosAuth
import requests
from itertools import islice

# Utility to chunk data
def chunk_data(data, chunk_size):
    it = iter(data)
    for first in it:
        yield [first] + list(islice(it, chunk_size - 1))

def sync_tai_data():
    base_url = "some_url"
    dataset = "system"
    columns = "system.system, system.con_id, system.primary_technology_owner, system.technology_owner, system.primary_business_owner, system.business_owner"
    url = f"{base_url}/{dataset}?c={columns}"

    print(f"Querying TAI API ({url}) ...")
    response = requests.get(url, auth=HTTPKerberosAuth(principal=""), timeout=60)
    data = response.json().get("data", [])
    data_count = response.json()['recorcount']

    # Fetch existing EON IDs directly as a set for faster lookups
    eonid_in_db = set(record["system.eon_id"] for record in tai_role_sync_data_col.find({}, {"eon_id": 1, "_id": 0}))

    # Extract EON IDs from API data
    eonid_in_tai = {record["system.eon_id"] for record in data}

    # Separate updates and inserts
    update_operations = []
    new_records = []

    for record in data:
        values_to_update = {
            "primary_technology_owner": record["system.primary_technology_owner"],
            "technology_owner": record["system.technology_owner"],
            "primary_business_owner": record["system.primary_business_owner"],
            "business_owner": record["system.business_owner"],
        }
        if record["system.eon_id"] in eonid_in_db:
            update_operations.append(
                UpdateOne(
                    {"eon_id": record["system.eon_id"]},
                    {"$set": values_to_update},
                    upsert=True
                )
            )
        else:
            values_to_insert = {
                "eon_id": record["system.eon_id"],
                **values_to_update,
            }
            new_records.append(values_to_insert)

    # Process updates in chunks
    chunk_size = 1000
    for chunk in chunk_data(update_operations, chunk_size):
        tai_role_sync_data_col.bulk_write(chunk)

    # Process inserts in chunks
    for chunk in chunk_data(new_records, chunk_size):
        tai_role_sync_data_col.insert_many(chunk)

    print("Sync completed successfully.")


</pre>
