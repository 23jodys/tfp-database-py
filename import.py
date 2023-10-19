from dotenv import load_dotenv
import os
import app.AirTable.tfp_air_table as Airtable


state_reps = Airtable.get_state_reps()
negative_bills = Airtable.get_negative_bills()
print(len(negative_bills))
print(negative_bills[:1])
