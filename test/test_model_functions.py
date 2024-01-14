from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
import pytest
from tfp_widget import models as m
import copy


TEST_REP_MODEL1 = m.Rep(id="Test1", name="Jane Doe", district="AL5")
TEST_REP_MODEL2 = m.Rep(id="Test2", name="Jane Doe", district="AL5")


@pytest.fixture()
def engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    m.Base.metadata.create_all(engine)

    yield engine

    m.Base.metadata.drop_all(bind=engine)









