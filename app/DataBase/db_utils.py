from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import os
import app.AirTable.tfp_air_table as Airtable
import pprint
import app.DataBase.models as Models


def bulk_upsert(at_records, engine, table_model):
    """Do a bulk upsert of a list of airtable records `at_records`
    into database `engine` and `table_model`.

    Uses the `id` field to detect conflicts. If there is a conflict
    this function *replaces* the existing record in the sql database.

    Args:
        at_records (list): list of records obtained from Airtable api.
        engine (sqlalchemy.engine): Database engine handle from `sqlalchemy.create_engine()`
        table_model (class): Abstract model class definition *not* an instance of a model.

    Example:
        `db_utils.bulk_upsert(state_reps, engine, Models.Rep)`
    """

    # Create a local alias for the low-level insert query
    # builder. sqlite and postgres support upsert functionality
    # mysql supports upsert using a different syntax.
    # sqlalchemy doesn't have a dialect-agnostic upsert (yet)

    # TODO Examine for refactor outside of the function.
    if engine.dialect.name == "sqlite":
        from sqlalchemy.dialects.sqlite import insert as upsert

    with Session(engine) as session:
        for at_record in at_records:
            try:
                local_rep = table_model()
                local_rep.from_airtable_record(at_record)
                row = local_rep.to_dict()

                # build a basic insert SQL statement
                stmt = upsert(table_model).values(row)

                # add an SQL clause for what to do if
                # there's a conflict using table_model.id
                stmt = stmt.on_conflict_do_update(
                    index_elements=[table_model.id], set_=row
                )

                session.execute(stmt)
                session.commit()

            # exception triggered when an at_record is missing
            # a required field.
            except KeyError as e:
                print(f"ERROR: Record missing required field: {e}")
                pprint.pprint(at_record)
                print("\n")

        total = session.query(table_model).count()

        print(f"Total: {total}")
