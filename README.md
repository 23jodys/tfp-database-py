# TFP Widgets v2

- Flask
- SQLAlchemy
- SQLAlchemy-Flask ORM
- Marshmallow
- Heroku

## Installation

```
git clone ...
cd tfp-database-py
python -m venv venv
source venv/bin/activate
pip install -r REQUIREMENTS.txt
```

## Development

### Run migrations

Uses Flask-Migrate (alembic)

To run migrations

```
flask --app "tfp_widget:create_app" db upgrade
```

To create new migrations after model changes

```shell
flask --app "tfp_widget:create_app" db migrate
```

### Airtable dumps
To develop, populate your `.env` with the following and add
your airtable credentials.

```python
# required token for authentication to airtable database
AIRTABLE_API_TOKEN="<token>"

# This value can be found off the API documentation site:
# https://airtable.com/appVXvrTCBaSvn2Id/api/docs
# id string of the database
AIRTABLE_BASE='appVXvrTCBaSvn2Id'

# a basic testing flag
# TESTING : use testing environment and database
# INTEGRATION_TESTING : testing using live servers and apis
# PRODUCTION : use production environment and database
RUN_ENV='TESTING'

# in-memory sqlite
TEST_DB='sqlite:///test.db'

# These values can be found off the API documentation site:
# https://airtable.com/appVXvrTCBaSvn2Id/api/docs
STATE_REPS_TABLE="tblcW1C6fiNHBnDaC"
NEGATIVE_BILLS_TABLE="tbl1tFOQZ1hepzpwa"
POSITIVE_BILLS_TABLE="tbldhR8N0Odf0z9ug"
NATIONAL_BILLS_TABLE="tblpupS2QgYmoOtbP"
NATIONAL_REPS_TABLE="tblK1MGo5pjIzfC6Z"
```

```shell
flask --app "tfp_widget:create_app" import-airtable-json --state-reps-file <from above> --national-reps-file <from above> \
--negative-bills-file <from above> --build-rep-relationships 
```

### Run in develop mode locally

```shell
FLASK_DEBUG=True flask --app "tfp_widget:create_app('development')" run
```

## Database

TODO document databse differences

## CI

TODO document how CI works in github

## Deployment

TODO document how we deploy to Heroku

## Roadmap

1. Get all importers working
   2. State Reps ✔ DONE
   3. Negative Bills DONE
   2. National Reps TODO
   3. Postive Bills TODO
2. Get the TFP api server working (flask) DONE
3. Migrate the client side stuff to be served by gunicorn or something. Need to merge the existing tfp-widgets repo. TODO
4. Setup Github CI to run tests DONE
5. Setup Github + Heroku to deploy branches to a testing environment
6. Setup Github + Heroku to deploy to production
5. New ways of viewing the data.
6. Performance improvements
