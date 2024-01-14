import logging
import pprint
from abc import abstractmethod
from typing import Optional
import json

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import select
import hashlib

from .database import db

LOGGER = logging.getLogger()


class Base:
    def to_dict(self):
        """Export data as plain python dict.

        Returns:
            dict: Python dict with database-relevant data.
        """

        return dict((col, getattr(self, col)) for col in self.__table__.columns.keys())

    def sha256(self):
        """
        Calculate the SHA-256 hash for the object.

        This method calculates the SHA-256 hash based on the sorted key-value pairs of the
        model object. The resulting hash is returned as a hexadecimal string.

        Note: The 'checksum' key is removed to prevent recursive checksums.

        Returns:
            str: The SHA-256 hash as a hexadecimal string.
        """

        self_dict = self.to_dict()
        # don't recheck the checksum to prevent recursive checksums
        del self_dict["checksum"]
        sorted_keys = sorted(self_dict.keys())

        return hashlib.sha256(
            "".join([str(self_dict.get(key, "")) for key in sorted_keys]).encode(
                "utf-8"
            )
        ).hexdigest()

    @classmethod
    def get_by_id(cls, id_to_find, session):
        rep_from_database = session.get(cls, id_to_find)
        return rep_from_database

    @staticmethod
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

    @classmethod
    def upsert(cls, at_record):
        """
        Upsert a record into the database.

        Args:
            cls (class): The class representing the database model.
            at_record (dict): The Airtable record to upsert.

        Returns:
            None

        Note:
            This method checks if the record already exists in the database. If it does,
            it updates the existing record with the data from the Airtable record. If the
            sha256 hash of the existing record is different from the new record, the existing
            record is updated. If the sha256 hashes match, the record is skipped. If the record
            does not exist in the database, a new instance is created and inserted.

            Does not commit, caller expected to commit.
        """
        found_instance = cls.query.get(at_record["id"])
        new_instance = cls.from_airtable_record(at_record)

        if found_instance:
            if found_instance.sha256 != new_instance.sha256:
                # Update the
                found_instance.from_airtable_record(at_record, found_instance)
                db.session.add(found_instance)
                LOGGER.debug("Upserted instance: {}".format(found_instance))
                return found_instance
            else:
                LOGGER.debug("Skipped instance: {}".format(new_instance))
                return found_instance
        else:
            db.session.add(new_instance)
            LOGGER.debug("Inserted instance: {}".format(new_instance))
            return new_instance

    @classmethod
    def bulk_upsert(cls, at_records):
        """Do a bulk upsert of a list of airtable records `at_records`

        Uses the `id` and sha256 field to detect conflicts. If there is a conflict
        this function *replaces* the existing record in the sql database.

        Args:
            at_records (list): list of records obtained from Airtable api.

        Example:
            `db_utils.bulk_upsert(state_reps)`
        """

        total_count = 0

        for at_record in at_records:
            try:
                cls.upsert(at_record=at_record)
                total_count += 1
            except KeyError as e:
                logging.error(
                    f"""ERROR: Record missing required field: {e}\n{pprint.pformat(at_record)}\n"""
                )
            if total_count % 100 == 0:
                logging.info(f"Total records inserted into {cls.__name__}: {total_count}")

        logging.info(f"Total records inserted into {cls.__name__}: {total_count}")

        db.session.commit()

    @abstractmethod
    def from_airtable_record(self, at_record):
        raise NotImplementedError()


class RepsToNegativeBills(db.Model, Base):
    """
    Representation of a many-to-many relationship between representatives and negative bills.

    Attributes:
        id (int): Unique identifier for this relationship.
        rep_id (str): Foreign key referencing the representative who is associated with this relationship.
        negative_bills_id (str): Foreign key referencing the negative bill that is associated with this relationship.
        relation_type (str): Type of relationship between the representative and the negative bill (e.g. "sponsor",
        "yeavote", etc.)
    """

    __tablename__ = "reps_to_negative_bills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rep_id: Mapped[str]
    negative_bills_id: Mapped[str]
    relation_type: Mapped[str]

    @classmethod
    def rep_build_all_relations(cls, at_reps, session):
        logger = logging.getLogger()
        total = {"yea_vote": 0, "nay_vote": 0, "sponsorship_vote": 0, "contact_bills": 0}
        last_total = 0
        for at_rep in at_reps:
            for yea_vote in at_rep.get("fields").get("Yea Votes", []):
                cls.rep_negative_bill_relation_insert(at_rep["id"], yea_vote, "yea_vote", session)
                total["yea_vote"] += 1
            for nay_vote in at_rep.get("fields").get("Nay Votes", []):
                cls.rep_negative_bill_relation_insert(at_rep["id"], nay_vote, "nay_vote", session)
                total["nay_vote"] += 1
            for sponsorship in at_rep.get("fields").get("Sponsorships", []):
                cls.rep_negative_bill_relation_insert(
                    at_rep["id"], sponsorship, "sponsorship", session
                )
                total["sponsorship_vote"] += 1
            for contact_bills in at_rep.get("fields").get("Bills to Contact about", []):
                cls.rep_negative_bill_relation_insert(
                    at_rep["id"], contact_bills, "contact", session
                )
                total["contact_bills"] += 1

            total_so_far = sum([y for x, y in total.items()])

            if total_so_far - last_total > 500:
                LOGGER.info(f"Total records inserted into {cls.__name__}: {total_so_far}")
                last_total = total_so_far

        db.session.commit()
        logger.info(
            f"Relationships created: yea_vote={total['yea_vote']}, nay_vote={total['nay_vote']}, \
            sponsorship_vote={total['sponsorship_vote']}, contact_bills={total['contact_bills']}")

    @classmethod
    def from_airtable_record(cls, at_record):
        raise NotImplementedError()

    @classmethod
    def rep_negative_bill_relation_insert(cls, rep_id, bill_id, rtype, session):
        # check for duplicate record
        existing_stmt = (
            select(cls)
            .where(cls.rep_id == rep_id)
            .where(cls.negative_bills_id == bill_id)
            .where(cls.relation_type == rtype)
        )

        if len(session.scalars(existing_stmt).all()) == 0:
            logging.debug(f"Adding bill relation: {rep_id}, {bill_id}, {rtype}")
            new_relation = cls()
            new_relation.rep_id = rep_id
            new_relation.negative_bills_id = bill_id
            new_relation.relation_type = rtype

            session.add(new_relation)


class Rep(db.Model, Base):
    __tablename__ = "reps"

    id: Mapped[str] = mapped_column(primary_key=True)
    # required fields
    name: Mapped[str]
    district: Mapped[str]
    role: Mapped[str]
    state: Mapped[str]

    # timestamps
    created: Mapped[str]
    modified: Mapped[str]

    political_party: Mapped[Optional[str]]
    reelection_date: Mapped[Optional[str]]
    website: Mapped[Optional[str]]

    # contact info
    email: Mapped[Optional[str]]
    facebook: Mapped[Optional[str]]
    twitter: Mapped[Optional[str]]
    capitol_address: Mapped[Optional[str]]
    capitol_phone: Mapped[Optional[str]]
    district_address: Mapped[Optional[str]]
    district_phone: Mapped[Optional[str]]

    # follow the money and legiscan
    ftm_eid: Mapped[Optional[int]]
    legiscan_id: Mapped[Optional[int]]
    checksum: Mapped[str] = mapped_column(index=True, unique=True)

    @classmethod
    def from_airtable_record(cls, at_record, existing_instance=None):
        """Imports airtable record mapping airtable fields to SQL columns.

        Args:
            at_record (dict): Nested dict representing an airtable data record.
            existing_instance: Optional existing instance to update when doing upserts

        Returns:
            NegativeBills: sqlalchemy model instance filled with data.
        """
        if not existing_instance:
            new_instance = cls()
        else:
            new_instance = existing_instance
        new_instance.id = at_record["id"]
        new_instance.name = at_record["fields"]["Name"]
        new_instance.district = at_record["fields"]["District"]
        new_instance.state = at_record["fields"]["State"]
        new_instance.role = at_record["fields"]["Role"]
        new_instance.created = at_record["fields"]["Created"]
        new_instance.modified = at_record["fields"]["Last Modified"]

        new_instance.political_party = at_record.get("fields").get("Political Party")
        new_instance.reelection_date = at_record.get("fields").get("Up For Reelection On")
        new_instance.website = at_record.get("fields").get("Website")
        new_instance.email = at_record.get("fields").get("Email")
        new_instance.facebook = at_record.get("fields").get("Facebook")
        new_instance.twitter = at_record.get("fields").get("Twitter")
        new_instance.capitol_address = at_record.get("fields").get("Capitol Address")
        new_instance.capitol_phone = at_record.get("fields").get("Capitol Phone Number")
        new_instance.district_address = at_record.get("fields").get("District Address")
        new_instance.district_phone = at_record.get("fields").get("District Phone Number")
        new_instance.ftm_eid = at_record.get("fields").get("Follow the Money EID")
        new_instance.legiscan_id = at_record.get("fields").get("Legiscan ID")
        new_instance.checksum = new_instance.sha256()

        # Do not commit the instance inside this function.
        return new_instance


class NegativeBills(db.Model, Base):
    __tablename__ = "negative_bills"
    id: Mapped[str] = mapped_column(primary_key=True)

    bill_information_link: Mapped[Optional[str]]
    case_name: Mapped[str]

    # TODO figure out whether this should be a json field
    category: Mapped[Optional[str]]
    expanded_category: Mapped[Optional[str]]
    created: Mapped[str]
    last_activity: Mapped[Optional[str]]
    last_modified: Mapped[Optional[str]]
    legiscan_id: Mapped[Optional[int]]
    progress: Mapped[Optional[str]]
    state: Mapped[str]
    status: Mapped[Optional[str]]
    summary: Mapped[Optional[str]]

    checksum: Mapped[str] = mapped_column(index=True, unique=True)

    @classmethod
    def from_airtable_record(cls, at_record, existing_instance=None):
        """Imports airtable record mapping airtable fields to SQL columns.

        Args:
            at_record (dict): Nested dict representing an airtable data record.
            existing_instance: Optional existing instance to modify when doing upsert

        Returns:
            NegativeBills: sqlalchemy model instance filled with data.
        """
        if not existing_instance:
            new_instance = cls()
        else:
            new_instance = existing_instance
        new_instance.id = at_record["id"]
        new_instance.created = at_record["createdTime"]
        new_instance.case_name = at_record["fields"]["Case Name"]
        new_instance.category = json.dumps(at_record["fields"].get("Category"))
        new_instance.expanded_category = json.dumps(at_record["fields"].get("Expanded Category"))
        new_instance.last_activity = at_record["fields"].get("Last Activity Date")
        new_instance.last_modified = at_record["fields"].get("Last Modified")
        new_instance.legiscan_id = at_record["fields"].get("Legiscan Bill ID")
        new_instance.progress = at_record["fields"].get("Progress")
        new_instance.state = at_record["fields"].get("State")
        new_instance.status = at_record["fields"].get("Status")
        new_instance.summary = at_record["fields"].get("Summary")
        new_instance.bill_information_link = at_record["fields"].get("Bill Information Link")

        new_instance.checksum = new_instance.sha256()

        return new_instance


negative_bills_json_example = """{'createdTime': '2023-04-11T23:16:25.000Z',
  'fields': {'Bill Information Link': 'https://legiscan.com/AL/bill/HB261/2023',
             'Case Name': 'AL HB261',
             'Category': ['Sports'],
             'Created': '2023-04-11T23:16:25.000Z',
             'Expanded Category': ['Sports'],
             'Last Activity Date': '2023-05-24',
             'Last Modified': '2023-09-25T20:56:30.000Z',
             'Legiscan Bill ID': 1753574,
             'Nay Votes': ['rec07tcDNbZB0V9Uq',
                           'recTly9LNN7KVg19B',
                           'recC8BwAbWZV7EpPJ',
                           'recDzxdwSVTtQlL82',
                           'rec6eVWRueAqzFsmw',
                           'reckthttps://en.wikipedia.org/wiki/Darko_SuvinFndwtWb991Mc',
                           'recIgprrXIoyvf8eK',
                           'recPbuM6HqRZ2483j'],
             'Progress': 'Passed',
             'Sponsors': ['recdlZiMsonXtuWS7'],
             'State': 'Alabama',
             'Status': 'Passed',
             'Summary': 'This bill expands existing legislation in Alabama '
                        'that restricts sports participation for trans '
                        'students in K-12 schools to include public 2- and 4- '
                        'year colleges and universities. The bill claims '
                        'various advantages to those who were assigned male at '
                        'birth. The bill prohibits someone the state claims to '
                        'be a "biological male" from joining a sports team for '
                        '"females," and vice versa. The bill prohibits '
                        'complaints to be filed about restrictions to K-12, '
                        'college, and/or university sports teams, or '
                        'retaliation towards anyone who files complaints. The '
                        'bill additionally provides recourse for complaints, '
                        'such as going to court for injunctive relief, '
                        'damages, and/or fees.',
             'Yea Votes': ['recLLmtQiKSgBr31n',
                            ...
                           'recfClzN6s7UUAIHF']},
  'id': 'rec03K3y0yLY6M31u'}"""

rep_json_example = """{'createdTime': '2023-03-29T22:00:53.000Z',
  'fields': {'Capitol Address': '24 Beacon St., Room 166, Boston, MA 02133',
             'Capitol Phone Number': '(617) 722-2692',
             'Created': '2023-03-29T22:00:53.000Z',
             'District': '6th Norfolk',
             'Email': 'William.Galvin@mahouse.gov',
             'Facebook': 'https://www.facebook.com/profile.php?id=100057703163724',
             'Follow the Money EID': 839710,
             'Last Modified': '2023-07-11T22:15:31.000Z',
             'Legiscan ID': 2441,
             'Name': 'William Galvin',
             'Political Party': 'Democrat',
             'Role': 'House Representative',
             'State': 'Massachusetts',
             'Up For Reelection On': '2022-11-05',
             'Website': 'https://malegislature.gov/Legislators/Profile/WCG1'},
  'id': 'rec02eJ7tvAv6H8LX'}"""
