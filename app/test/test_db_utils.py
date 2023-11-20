from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import app.DataBase.db_utils as db_utils
import pytest
import app.DataBase.models as Models
from sqlalchemy.orm import sessionmaker
import copy
import logging


def test_test():
    assert True


negative_bills_json_example = {
    "createdTime": "2023-04-11T23:16:25.000Z",
    "fields": {
        "Bill Information Link": "https://legiscan.com/AL/bill/HB261/2023",
        "Case Name": "AL HB261",
        "Category": ["Sports"],
        "Created": "2023-04-11T23:16:25.000Z",
        "Expanded Category": ["Sports"],
        "Last Activity Date": "2023-05-24",
        "Last Modified": "2023-09-25T20:56:30.000Z",
        "Legiscan Bill ID": 1753574,
        "Nay Votes": [
            "rec07tcDNbZB0V9Uq",
            "recTly9LNN7KVg19B",
            "recC8BwAbWZV7EpPJ",
            "recDzxdwSVTtQlL82",
            "rec6eVWRueAqzFsmw",
            "reckthttps://en.wikipedia.org/wiki/Darko_SuvinFndwtWb991Mc",
            "recIgprrXIoyvf8eK",
            "recPbuM6HqRZ2483j",
        ],
        "Progress": "Passed",
        "Sponsors": ["recdlZiMsonXtuWS7"],
        "State": "Alabama",
        "Status": "Passed",
        "Summary": "This bill expands existing legislation in Alabama ",
        "Yea Votes": ["recLLmtQiKSgBr31n", "recfClzN6s7UUAIHF"],
    },
    "id": "rec03K3y0yLY6M31u",
}


rep_json_example = {
    "createdTime": "2023-03-29T22:00:53.000Z",
    "fields": {
        "Capitol Address": "24 Beacon St., Room 166, Boston, MA 02133",
        "Capitol Phone Number": "(617) 722-2692",
        "Created": "2023-03-29T22:00:53.000Z",
        "District": "6th Norfolk",
        "Email": "William.Galvin@mahouse.gov",
        "Facebook": "https://www.facebook.com/profile.php?id=100057703163724",
        "Follow the Money EID": 839710,
        "Last Modified": "2023-07-11T22:15:31.000Z",
        "Legiscan ID": 2441,
        "Name": "William Galvin",
        "Political Party": "Democrat",
        "Role": "House Representative",
        "State": "Massachusetts",
        "Up For Reelection On": "2022-11-05",
        "Website": "https://malegislature.gov/Legislators/Profile/WCG1",
    },
    "id": "rec02eJ7tvAv6H8LX",
}


def test_negative_bills_json():
    assert negative_bills_json_example.get("id") == "rec03K3y0yLY6M31u"


def test_rep_json():
    assert rep_json_example.get("id") == "rec02eJ7tvAv6H8LX"


@pytest.fixture()
def engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Models.Base.metadata.create_all(engine)

    yield engine

    Models.Base.metadata.drop_all(bind=engine)


def test_search_rep_by_id_returns_negative(engine):
    with Session(engine) as session:
        rep_id = rep_json_example["id"]
        assert db_utils.get_rep_by_id(rep_id, session) is None


def test_insert_and_search_single_rep(engine):
    with Session(engine) as session:
        db_utils.insert_rep(rep_json_example, session)
        from_db = db_utils.get_rep_by_id(rep_json_example["id"], session)
        assert from_db is not None
        assert from_db.id == "rec02eJ7tvAv6H8LX"


def test_insert_then_update_rep(engine):
    with Session(engine) as session:
        db_utils.insert_rep(rep_json_example, session)
        mod_at_record = copy.deepcopy(rep_json_example)
        mod_at_record["fields"]["Name"] = "A Quick Brown Fox"

        db_utils.update_rep(mod_at_record, session)

        session.commit()

    with Session(engine) as session:
        from_db = db_utils.get_rep_by_id(rep_json_example["id"], session)
        assert from_db.name == "A Quick Brown Fox"


def test_insert_skip_then_update_rep(engine):
    with Session(engine) as session:
        # fresh database, should insert
        insert_status = db_utils.insert_or_update_rep(rep_json_example, session)

        # repeated insert attempts should skip
        skip_status = db_utils.insert_or_update_rep(rep_json_example, session)

        # deepcopy to not modify original
        mod_at_record = copy.deepcopy(rep_json_example)
        mod_at_record["fields"]["Name"] = "A Quick Brown Fox"

        # modified at_record should trigger update
        update_status = db_utils.insert_or_update_rep(mod_at_record, session)

        assert insert_status == "insert"
        assert skip_status == "skip"
        assert update_status == "update"

        from_db = db_utils.get_rep_by_id(rep_json_example["id"], session)
        assert from_db.name == "A Quick Brown Fox"
