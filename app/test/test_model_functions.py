import os
import pytest
import app.DataBase.models as Models
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import app.DataBase.db_utils as db_utils
import pytest
import app.DataBase.models as Models
from sqlalchemy.orm import sessionmaker
import copy
import logging


TEST_REP_MODEL1 = Models.Rep(id="Test1", name="Jane Doe", district="AL5")
TEST_REP_MODEL2 = Models.Rep(id="Test2", name="Jane Doe", district="AL5")


def test_get_sha256():
    checksum = TEST_REP_MODEL1.sha256()
    print(checksum)
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


@pytest.fixture()
def engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Models.Base.metadata.create_all(engine)

    yield engine

    Models.Base.metadata.drop_all(bind=engine)
