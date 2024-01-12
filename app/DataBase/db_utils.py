from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import app.AirTable.tfp_air_table as Airtable
import pprint
import app.DataBase.models as Models
import logging
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)


def error_logger(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Error occurred: {e}")
            # You can also log the error or send an email or whatever
            # you want to do in case of an exception
            return None  # or some default value

    return wrapper


load_dotenv()

if os.getenv("RUN_ENV") == "TESTING":
    DB_URI = os.getenv("TEST_DB")
elif os.getenv("RUN_ENV") == "INTEGRATION_TESTING":
    DB_URI = os.getenv("TEST_DB")

engine = db.engine
#Models.Base.metadata.create_all(engine)


def get_upsert_builder(engine):
    """
    Dynamically retrieves the appropriate upsert builder function based on the provided engine's dialect.

    Args:
        engine: A SQLAlchemy engine object.

    Returns:
        A function object corresponding to the upsert builder for the dialect.

    Raises:
        NotImplementedError: If the dialect does not currently support upsert functionality.

    Supported Dialects:
        - sqlite: Uses `sqlalchemy.dialects.sqlite.insert`
        - postgresql: Uses `sqlalchemy.dialects.postgresql.insert`
        - mysql: Not yet implemented (specific syntax required)
    """
    if engine.dialect.name == "sqlite":
        from sqlalchemy.dialects.sqlite import insert as upsert
    elif engine.dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert as upsert
    else:
        raise NotImplementedError("Upsert not supported for this dialect")
    return upsert


#upsert = get_upsert_builder(engine)

#Session = sessionmaker(engine)


def bulk_upsert(at_records, table_model, session):
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

    for at_record in at_records:
        try:
            local_rep = table_model()
            local_rep.from_airtable_record(at_record)
            row = local_rep.to_dict()

            # build a basic insert SQL statement
            stmt = get_upsert_builder(db.engine)(session.table_model).values(row)

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


@error_logger
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
        logging.debug(f"Adding bill relation: {rep_id}, {bill_id}, {rtype}")
        new_relation = join_table(
            rep_id=rep_id, negative_bills_id=bill_id, relation_type=rtype
        )

        session.add(new_relation)


@error_logger
def rep_build_all_relations(at_rep, session):
    for yea_vote in at_rep.get("fields").get("Yea Votes", []):
        rep_negative_bill_relation_insert(at_rep["id"], yea_vote, "yea_vote", session)
    for nay_vote in at_rep.get("fields").get("Nay Votes", []):
        rep_negative_bill_relation_insert(at_rep["id"], nay_vote, "nay_vote", session)
    for sponsorship in at_rep.get("fields").get("Sponsorships", []):
        rep_negative_bill_relation_insert(
            at_rep["id"], sponsorship, "sponsorship", session
        )
    for contact_bills in at_rep.get("fields").get("Bills to Contact about", []):
        rep_negative_bill_relation_insert(
            at_rep["id"], contact_bills, "contact", session
        )


def get_rep_by_id(id, session):
    rep_from_database = Models.Rep.get_by_id(id, session)
    return rep_from_database


def insert_rep(at_rep, session):
    new_rep = Models.Rep().from_airtable_record(at_rep)
    session.add(new_rep)
    session.commit()


def update_rep(at_rep, session):
    """
    Updates a Representative (Rep) object in the database using data from an Airtable record.

    Args:
        at_rep (dict): An Airtable record representing a Representative.
        session (SQLAlchemy Session): An active SQLAlchemy session.

    Returns:
        None

    Description:
        This function takes an Airtable record representing a Representative and updates the corresponding
        Representative object in the database.
    """
    new_rep = Models.Rep().from_airtable_record(at_rep)
    rep_from_db = get_rep_by_id(at_rep["id"], session)

    for key, value in new_rep.to_dict().items():
        setattr(rep_from_db, key, value)

    session.commit()


def insert_or_update_rep(at_rep, session):
    """
    Inserts or updates a `Rep` record in the database, based on comparison with Airtable data.

    Args:
        at_rep (dict): A dictionary representing a single Airtable record for a `Rep`.
        session: An active database session object, used for querying and persistence.

    Returns:
        str: One of "insert", "update", or "skip", indicating the action taken.

        - "insert": Record was created as it didn't exist yet.
        - "update": Existing record was modified due to Airtable data change.
        - "skip": No change, Airtable data matches the database record.

    """

    new_rep = Models.Rep().from_airtable_record(at_rep)
    id = new_rep.id
    rep_from_database = session.query(Models.Rep).filter(Models.Rep.id == id).first()

    if rep_from_database is None:
        insert_rep(at_rep, session)
        return "insert"
    elif new_rep.checksum != rep_from_database.checksum:
        update_rep(at_rep, session)
        return "update"
    else:
        return "skip"
