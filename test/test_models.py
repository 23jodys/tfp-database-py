import copy
from unittest.mock import patch

from tfp_widget import create_app
from tfp_widget.database import db
from tfp_widget.models import Rep, RepsToNegativeBills

app = create_app("testing")

TEST_REP_MODEL1 = Rep()
TEST_REP_MODEL1.id = "Test1"
TEST_REP_MODEL1.name = "Jane Doe"
TEST_REP_MODEL1.district = "AL5"

TEST_REP_MODEL2 = Rep()
TEST_REP_MODEL2.id = "Test2"
TEST_REP_MODEL2.name = "Jane Doe"
TEST_REP_MODEL2.district = "AL5"

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


def test_get_sha256():
    checksum = TEST_REP_MODEL1.sha256()
    assert (
            checksum == "2b0f97527663a16ff611a621d6f86ff966705ac7918d08d7c3e69a35f611cd1a"
    )


def test_sha256_is_different():
    checksum1 = TEST_REP_MODEL1.sha256()
    checksum2 = TEST_REP_MODEL2.sha256()
    assert checksum1 != checksum2


def test_to_dict():
    test_dict = TEST_REP_MODEL1.to_dict()
    assert test_dict.get("id") == "Test1"
    assert test_dict.get("name") == "Jane Doe"
    assert test_dict.get("district") == "AL5"


def test_rep_upsert_no_record_found_do_insert(client):
    """Given that no record is in the database, it should create a new record."""
    with app.app_context():
        with patch('tfp_widget.models.LOGGER') as mock_logger:
            Rep.upsert(at_record=rep_json_example)

            assert Rep.query.get(rep_json_example["id"]) is not None
            mock_logger.debug.assert_called_once()


def test_rep_upsert_with_existing_record(client):
    """
    Given an already existing record, attempt to update the name. Verify that the record
    was updated in place with the correct name and that there are not two records.
    """
    with app.app_context():
        at_record_old = rep_json_example
        old_result = Rep.upsert(at_record=at_record_old)
        db.session.add(old_result)
        db.session.commit()

        at_record_new = copy.deepcopy(rep_json_example)
        at_record_new["fields"]["Name"] = "Winifred Galvin"
        new_result = Rep.upsert(at_record=at_record_new)
        db.session.add(new_result)
        db.session.commit()

        observed_winifred = Rep.query.filter_by(name="Winifred Galvin")
        assert observed_winifred.count() == 1, "There should only be one Winifred record"
        observed_william = Rep.query.filter_by(name="William Galvin")
        assert observed_william.count() == 0, "There should be no William record because we overwrote it"


def test_rep_upsert_no_changes(client):
    """
    Given an existing representative record in the database with the name "William Galvin",
    verify that when an identically valued record is upserted, there is still only
    one representative with the name "William Galvin" in the database.
    """
    with app.app_context():
        at_record_old = rep_json_example
        old_result = Rep.upsert(at_record=at_record_old)
        db.session.add(old_result)
        db.session.commit()

        at_record_old = rep_json_example
        old_result = Rep.upsert(at_record=at_record_old)
        db.session.add(old_result)
        db.session.commit()

        observed_william = Rep.query.filter_by(name="William Galvin")
        assert observed_william.count() == 1, "There should be only one William record"


def test_relation_insert(client):
    with app.test_client():
        RepsToNegativeBills.rep_negative_bill_relation_insert("foo", "bar", "test", db.session)
        db.session.commit()
        result = RepsToNegativeBills.query.filter_by(rep_id="foo").first()
        assert result.rep_id == "foo"
        assert result.negative_bills_id == "bar"
        assert result.relation_type == "test"


def test_insert_of_multiple_relations(client):
    rep = copy.deepcopy(rep_json_example)
    rep["fields"]["Yea Votes"] = ["Yea1", "Yea2"]
    rep["fields"]["Nay Votes"] = ["Nay", "Nay2"]
    rep["fields"]["Bills to Contact about"] = ["Contact1", "Contact2"]
    rep["fields"]["Sponsorships"] = ["Sponsor1", "Sponsor2"]

    with app.app_context():
        RepsToNegativeBills.rep_build_all_relations([rep], db.session)
        db.session.commit()

        results = RepsToNegativeBills.query.filter_by(rep_id=rep["id"])
        assert results.count() == 8

        results = RepsToNegativeBills.query.filter_by(rep_id=rep["id"], relation_type="yea_vote")
        assert results.count() == 2

        results = RepsToNegativeBills.query.filter_by(rep_id=rep["id"], relation_type="nay_vote")
        assert results.count() == 2

        results = RepsToNegativeBills.query.filter_by(rep_id=rep["id"], relation_type="sponsorship")
        assert results.count() == 2

        results = RepsToNegativeBills.query.filter_by(rep_id=rep["id"], relation_type="contact")
        assert results.count() == 2


def test_insert_of_relations_no_relations(client):
    """A rep with no relations shouldn't trigger an exception, nor
    insert records."""
    with app.app_context():
        RepsToNegativeBills.rep_build_all_relations([rep_json_example], db.session)
        db.session.commit()

        results = RepsToNegativeBills.query.filter_by(rep_id=rep_json_example["id"])
        assert results.count() == 0
