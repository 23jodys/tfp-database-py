import logging
import pprint
from abc import abstractmethod
from typing import Optional
import json

import sqlalchemy.orm
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import select
import hashlib



class Base(DeclarativeBase):
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
        # don't recheck the checksum to prevent recursive checksumsums
        del self_dict["checksum"]
        sorted_keys = sorted(self_dict.keys())

        return hashlib.sha256(
            "".join([str(self_dict.get(key, "")) for key in sorted_keys]).encode(
                "utf-8"
            )
        ).hexdigest()

    @classmethod
    def get_by_id(cls, id, session):
        rep_from_database = session.get(cls, id)
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

    def bulk_upsert(self, session: sqlalchemy.orm.Session, at_records):
        """Do a bulk upsert of a list of airtable records `at_records`
        into database `engine` and `table_model`.

        Uses the `id` field to detect conflicts. If there is a conflict
        this function *replaces* the existing record in the sql database.

        Args:
            session (sqlalchemy.orm): A SQLAlchemy database session
            at_records (list): list of records obtained from Airtable api.

        Example:
            `db_utils.bulk_upsert(state_reps, engine, Models.Rep)`
        """

        for at_record in at_records:
            try:
                self.from_airtable_record(at_record)
                row = self.to_dict()

                # build a basic insert SQL statement
                upsert = self.get_upsert_builder(session.get_bind())
                stmt = upsert(self.__class__).values(row)

                # add an SQL clause for what to do if
                # there's a conflict using table_model.id
                stmt = stmt.on_conflict_do_update(
                    index_elements=[self.__class__.id], set_=row
                )

                session.execute(stmt)
                session.commit()

            # exception triggered when an at_record is missing
            # a required field.
            except KeyError as e:
                logging.error(
                    f"""ERROR: Record missing required field: {e}\n{pprint.pformat(at_record)}\n"""
                )

        total = session.query(self.__class__).count()
        logging.info(f"Total records inserted: {total}")

    @abstractmethod
    def from_airtable_record(self, at_record):
        raise NotImplementedError()


class RepsToNegativeBills(Base):
    """
    Representation of a many-to-many relationship between representatives and negative bills.

    Attributes:
        id (int): Unique identifier for this relationship.
        rep_id (str): Foreign key referencing the representative who is associated with this relationship.
        negative_bills_id (str): Foreign key referencing the negative bill that is associated with this relationship.
        relation_type (str): Type of relationship between the representative and the negative bill (e.g. "sponsor", "yeavote", etc.)
    """

    __tablename__ = "reps_to_negative_bills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rep_id: Mapped[str]
    negative_bills_id: Mapped[str]
    relation_type: Mapped[str]

    @classmethod
    def rep_build_all_relations(cls, at_reps, session):
        logger = logging.getLogger()
        total = {}
        total["yea_vote"] = 0
        total["nay_vote"] = 0
        total["sponsorship_vote"] = 0
        total["contact_bills"] = 0
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
            if total_so_far % 100 == 0:
                print("Processed {} records".format(total_so_far))


        session.commit()
        logger.info(f"Relationships created: yea_vote={total['yea_vote']}, nay_vote={total['nay_vote']}, sponsorship_vote={total['sponsorship_vote']}, contact_bills={total['contact_bills']}")

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
            new_relation = cls(
                rep_id=rep_id, negative_bills_id=bill_id, relation_type=rtype
            )

            session.add(new_relation)

class Rep(Base):
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

    def from_airtable_record(self, at_rep):
        """Imports airtable record mapping airtable fields to SQL columns.

        Args:
            at_rep (dict): Nested dict representing an airtable data record.

        Returns:
            NegativeBills: sqlalchemy model instance filled with data.
        """

        self.id = at_rep["id"]
        self.name = at_rep["fields"]["Name"]
        self.district = at_rep["fields"]["District"]
        self.state = at_rep["fields"]["State"]
        self.role = at_rep["fields"]["Role"]
        self.created = at_rep["fields"]["Created"]
        self.modified = at_rep["fields"]["Last Modified"]

        self.political_party = at_rep.get("fields").get("Political Party")
        self.reelection_date = at_rep.get("fields").get("Up For Reelection On")
        self.website = at_rep.get("fields").get("Website")
        self.email = at_rep.get("fields").get("Email")
        self.facebook = at_rep.get("fields").get("Facebook")
        self.twitter = at_rep.get("fields").get("Twitter")
        self.capitol_address = at_rep.get("fields").get("Capitol Address")
        self.capitol_phone = at_rep.get("fields").get("Capitol Phone Number")
        self.district_address = at_rep.get("fields").get("District Address")
        self.district_phone = at_rep.get("fields").get("District Phone Number")
        self.ftm_eid = at_rep.get("fields").get("Follow the Money EID")
        self.legiscan_id = at_rep.get("fields").get("Legiscan ID")
        self.checksum = self.sha256()

        return self



class NegativeBills(Base):
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

    def from_airtable_record(self, at_bill):
        """Imports airtable record mapping airtable fields to SQL columns.

        Args:
            at_bill (dict): Nested dict representing an airtable data record.

        Returns:
            NegativeBills: sqlalchemy model instance filled with data.
        """
        self.id = at_bill["id"]
        self.created = at_bill["createdTime"]
        self.case_name = at_bill["fields"]["Case Name"]
        self.category = json.dumps(at_bill["fields"].get("Category"))
        self.expanded_category = json.dumps(at_bill["fields"].get("Expanded Category"))
        self.last_activity = at_bill["fields"].get("Last Activity Date")
        self.last_modified = at_bill["fields"].get("Last Modified")
        self.legiscan_id = at_bill["fields"].get("Legiscan Bill ID")
        self.progress = at_bill["fields"].get("Progress")
        self.state = at_bill["fields"].get("State")
        self.status = at_bill["fields"].get("Status")
        self.summary = at_bill["fields"].get("Summary")
        self.bill_information_link = at_bill["fields"].get("Bill Information Link")

        self.checksum = self.sha256()

        return self


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
