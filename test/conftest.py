import pytest
from tfp_widget import create_app
from tfp_widget.database import db


@pytest.fixture(autouse=True)
def client():
    app = create_app("testing")
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client

            db.session.remove()
            db.drop_all()
