from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import app.AirTable.tfp_air_table as Airtable
import pprint
import app.DataBase.models as Models
import app.DataBase.db_utils as db_utils


state_reps = Airtable.get_state_reps()
national_reps = Airtable.get_national_reps()
negative_bills = Airtable.get_negative_bills()

# database setup


db_utils.bulk_upsert(state_reps, Models.Rep)
db_utils.bulk_upsert(negative_bills, Models.NegativeBills)
