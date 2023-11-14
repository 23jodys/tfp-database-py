from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import os
import app.AirTable.tfp_air_table as Airtable
import pprint
import app.DataBase.models as Models
import logging
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)


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
                logging.error(
                    f"""ERROR: Record missing required field: {e}\n{pprint.pformat(at_record)}\n"""
                )

        total = session.query(table_model).count()

        logging.info(f"Total records inserted: {total}")


def rep_negative_bill_relation_insert(rep_id, bill_id, rtype, session):
    join_table = Models.RepsToNegativeBills
    # check for duplicate record
    existing_stmt = (
        select(join_table)
        .where(join_table.rep_id == rep_id)
        .where(join_table.negative_bills_id == bill_id)
        .where(join_table.relation_type == rtype)
    )

    if len(session.scalars(existing_stmt).all()) == 0:
        logging.info(f"Adding bill relation: {rep_id}, {bill_id}, {rtype}")
        new_relation = join_table(
            rep_id=rep_id, negative_bills_id=bill_id, relation_type=rtype
        )

        session.add(new_relation)
        session.commit()
