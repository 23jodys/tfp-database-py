import json

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import app.AirTable.tfp_air_table as Airtable
import pprint
import app.DataBase.models as Models
#import app.DataBase.db_utils as db_utils
import logging
import time

logging.basicConfig(level=logging.INFO)

load_dotenv()

from app.api import db

at_data = {}
at_data["state_reps"] = Airtable.get_state_reps()
at_data["national_reps"] = Airtable.get_national_reps()
at_data["negative_bills"] = Airtable.get_negative_bills()

unix_timestamp = int(time.time())
for table_name, table in at_data.items():
    with open(f"{table_name}_{unix_timestamp}.json", "w") as storage:
        json.dump(table, storage)

# database setup
#db_utils.bulk_upsert(state_reps, Models.Rep, session)
#db.models.Reps.bulk_upsert(db.session, state_reps)
#db_utils.bulk_upsert(negative_bills, Models.NegativeBills, session)

#for rep in state_reps:
#    db_utils.rep_build_all_relations(rep, db.session)
#    db.session.commit()