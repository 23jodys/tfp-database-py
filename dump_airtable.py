import json

from dotenv import load_dotenv
import tfp_widget.airtable.tfp_air_table as airtable
import logging
import time

logging.basicConfig(level=logging.INFO)

load_dotenv()

at_data = {
    "state_reps": airtable.get_state_reps(),
    "national_reps": airtable.get_national_reps(),
    "negative_bills": airtable.get_negative_bills()
}

unix_timestamp = int(time.time())
for table_name, table in at_data.items():
    with open(f"{table_name}_{unix_timestamp}.json", "w") as storage:
        json.dump(table, storage)