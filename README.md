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
from concurrent.futures import ThreadPoolExecutor

def sync_tai_data():
    base_url = "some_url"
    dataset = "system"
    columns = "system.system, system.eon_id, system.primary_technology_owner, system.technology_owner, system.primary_business_owner, system.business_owner"
    url = f"{base_url}/{dataset}?c={columns}"

    print(f"Querying TAI API ({url}) ...")
    response = requests.get(url, auth=HTTPKerberosAuth(principal=""), timeout=60)
    data = response.json().get("data", [])

    if not data:
        print("No data retrieved from the API.")
        return

    # Get all eonids in one query
    eonid_in_db = {
        record["eon_id"]
        for record in tai_role_sync_data_col.find({}, {"eon_id": 1, "_id": 0})
    }

    # Split data into update and insert sets
    update_operations = []
    insert_data = []

    for record in data:
        values = {
            "primary_technology_owner": record["system.primary_technology_owner"],
            "technology_owner": record["system.technology_owner"],
            "primary_business_owner": record["system.primary_business_owner"],
            "business_owner": record["system.business_owner"],
        }

        if record["system.eon_id"] in eonid_in_db:
            update_operations.append(
                UpdateOne(
                    {"eon_id": record["system.eon_id"]},
                    {"$set": values},
                    upsert=True
                )
            )
        else:
            values["eon_id"] = record["system.eon_id"]
            insert_data.append(values)

    # Parallel execution of updates and inserts
    with ThreadPoolExecutor(max_workers=2) as executor:
        if update_operations:
            executor.submit(process_updates, update_operations)
        if insert_data:
            executor.submit(process_inserts, insert_data)

    print("Sync completed successfully.")

def process_updates(operations):
    tai_role_sync_data_col.bulk_write(operations)
    print(f"Updated {len(operations)} records.")

def process_inserts(data):
    tai_role_sync_data_col.insert_many(data)
    print(f"Inserted {len(data)} new records.")


</pre>
