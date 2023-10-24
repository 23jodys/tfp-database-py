from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import os
import app.AirTable.tfp_air_table as Airtable
import pprint
import app.DataBase.models as Models

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


with Session(engine) as session:
    for at_rep in state_reps:
        try:
            local_rep = Models.Rep()
            local_rep.from_airtable_record(at_rep)
            row = local_rep.to_dict()

            pprint.pprint(row)

            stmt = upsert(Models.Rep).values(row)
            stmt = stmt.on_conflict_do_update(index_elements=[Models.Rep.id], set_=row)

            session.execute(stmt)
            session.commit()
        except KeyError as e:
            print(f"ERROR: Record missing required field: {e}")
            pprint.pprint(at_rep)
            print("\n")

    total = session.query(Models.Rep).count()

    print(f"Total: {total}")
