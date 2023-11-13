from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import os
import app.AirTable.tfp_air_table as Airtable
import pprint
import app.DataBase.models as Models
import app.DataBase.db_utils as db_utils

load_dotenv()

if os.getenv("RUN_ENV") == "TESTING":
    DB_URI = os.getenv("TEST_DB")
elif os.getenv("RUN_ENV") == "INTEGRATION_TESTING":
    DB_URI = os.getenv("TEST_DB")


state_reps = Airtable.get_state_reps()
national_reps = Airtable.get_national_reps()
negative_bills = Airtable.get_negative_bills()

# database setup
engine = create_engine(DB_URI, echo=False)
Models.Base.metadata.create_all(engine)
print(engine.dialect.name)
if engine.dialect.name == "sqlite":
    from sqlalchemy.dialects.sqlite import insert as upsert


db_utils.bulk_upsert(state_reps, engine, Models.Rep)
db_utils.bulk_upsert(negative_bills, engine, Models.NegativeBills)

# TODO: Review sqlalchemy documentation on many-to-many relationships
# TODO: Build affinity table model.
