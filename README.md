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

def sync_tai_data():
    base_url = "some_url"
    dataset = "system"
    columns = "system.system, system.con_id, system.primary_technology_owner, system.technology_owner, system.primary_business_owner, system.business_owner"
    url = f"{base_url}/{dataset}?c={columns}"

    print(f"Querying TAI API ({url}) ...")
    response = requests.get(url, auth=HTTPKerberosAuth(principal=""), timeout=60)
    data = response.json().get("data", [])

    if not data:
        print("No data received from TAI API.")
        return

    # Fetch existing EON IDs from the database
    eonid_in_db = {
        record["system.eon_id"] for record in tai_role_sync_data_col.find({}, {"system.eon_id": 1, "_id": 0})
    }

    # Lambda to construct update values
    construct_update_values = lambda record: {
        "primary_technology_owner": record["system.primary_technology_owner"],
        "technology_owner": record["system.technology_owner"],
        "primary_business_owner": record["system.primary_business_owner"],
        "business_owner": record["system.business_owner"],
    }

    # Separate records into updates and inserts
    update_operations = []
    insert_data = []

    for record in data:
        if record["system.eon_id"] in eonid_in_db:
            # Update operation for existing EON IDs
            update_operations.append(
                UpdateOne(
                    {"system.eon_id": record["system.eon_id"]},
                    {"$set": construct_update_values(record)},
                    upsert=True
                )
            )
        else:
            # Insert operation for new EON IDs
            insert_data.append({
                "system.eon_id": record["system.eon_id"],
                **construct_update_values(record),
            })

    # Execute all updates in a single bulk_write operation
    if update_operations:
        tai_role_sync_data_col.bulk_write(update_operations)

    # Insert new data in a single insert_many operation
    if insert_data:
        tai_role_sync_data_col.insert_many(insert_data)

    print("Sync completed successfully.")



</pre>
