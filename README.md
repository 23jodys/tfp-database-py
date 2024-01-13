# AirTable to SQL Importer for TransFormations Project: Python

An attempt to get momentum on the Widget database.

## Installation/Development

```
git clone ...
cd tfp-database-py
python -m venv venv
source venv/bin/activate
pip install -r REQUIREMENTS.txt
```

Currently tested using `Python 3.10.12`

## Database

RUN_ENV=dev|prod

Will use a sqlite database in dev and the heroku database in prod (DATABASE_URL).

### Migrations

Uses Flask-Migrate (alembic)

To run migrations

```
cd app
flask --app api db upgrade
```

To create new migrations after model changes

```shell
cd app
flask --app api db migrate
```

### Importing airtable

This is broken into two pieces: creating JSON blobs with all of the data from airtable
and actually ingesting into the database and creating relationships.


```shell
cd tfp-database-py
flask --app app/api import-airtable-json --state-reps-file <from above> --national-reps-file <from above> \
--negative-bills-file <from above> --build-rep-relationships TRUE
```

#### Production

## Roadmap

1. Get all importers working
2. Get the TFP api server working (flask)
3. Deployment
4. ...
5. New ways of viewing the data.
6. Performance improvements
7.
