from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import app.AirTable.tfp_air_table as Airtable
import pprint
import app.DataBase.models as Models
import app.DataBase.db_utils as db_utils
import logging

logging.basicConfig(level=logging.INFO)


load_dotenv()

if os.getenv("RUN_ENV") == "TESTING":
    DB_URI = os.getenv("TEST_DB")
elif os.getenv("RUN_ENV") == "INTEGRATION_TESTING":
    DB_URI = os.getenv("TEST_DB")

engine = create_engine(DB_URI, echo=False)

# only runs if models don't currently exist
Models.Base.metadata.create_all(engine)
Session = sessionmaker(engine)

state_reps = Airtable.get_state_reps()
national_reps = Airtable.get_national_reps()
negative_bills = Airtable.get_negative_bills()

# database setup


db_utils.bulk_upsert(state_reps, Models.Rep)
db_utils.bulk_upsert(negative_bills, Models.NegativeBills)

with Session() as session:
    for rep in state_reps:
        db_utils.rep_build_all_relations(rep, session)
        session.commit()
