import logging
import os

from flask import Flask
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_restful import Api

from . import database
from . import models as m
from . import views
from .commands import import_airtable_json


class Config:
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.abspath(os.getcwd()) + "/test.db"


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:/'


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', "").replace("postgres://", "postgresql://", 1)


config_by_name = dict(
    development=DevelopmentConfig,
    testing=TestingConfig,
    production=ProductionConfig,
)


def create_app(config_name="development"):
    for key, value in os.environ.items():
        print(f"{key}={value}")
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    CORS(app)
    #if app.debug:
    logging.basicConfig(level=logging.INFO)

    Migrate(app, database.db)

    database.db.init_app(app)

    Marshmallow(app)
    api = Api(app)

    api.add_resource(views.RepsResource, '/api/reps/search/<string:search_query>')

    app.cli.add_command(import_airtable_json)

    return app
