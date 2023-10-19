from dotenv import load_dotenv
import os
from app.AirTable.tfp_air_table import get_state_reps

load_dotenv()

AIRTABLE_API_TOKEN = os.getenv("AIRTABLE_API_TOKEN")
AIRTABLE_BASE = os.getenv("AIRTABLE_BASE")

AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE}"

reps = get_state_reps(AIRTABLE_URL, AIRTABLE_API_TOKEN)
print(len(reps))
print(reps[:1])
