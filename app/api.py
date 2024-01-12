import json
import logging
import os
from collections import defaultdict

import click
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from marshmallow import ValidationError, fields
from sqlalchemy import or_, and_

from app.DataBase import models as m

logging.getLogger().setLevel(logging.INFO)

app = Flask(__name__)
CORS(app)

load_dotenv()

if os.getenv('RUN_ENV', "dev") == 'dev':
    DB_URI = 'sqlite:///' + os.path.abspath(os.getcwd())  + "/test.db"
elif os.getenv('RUN_ENV') == 'prod':
    DB_URI = os.getenv('DATABASE_URL').replace("postgres://", "postgresql://", 1)
else:
    raise Exception("HOLY SHIT")

app.config["SQLALCHEMY_DATABASE_URI"] = DB_URI

db = SQLAlchemy(model_class=m.Base)

migrate = Migrate(app, db)

db.init_app(app)

ma = Marshmallow(app)
api = Api(app)

class NegativeBillsSchema(ma.SQLAlchemyAutoSchema):
    pass

class RepSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        fields = (
            "id",
            "name",
            "state",
            "district",
            "affiliation",
            "role",
            "email",
            "capitolPhoneNumber",
            "districtPhoneNumber",
            "twitterUrl",
            "billsSponsored",
            "billsYeaVotes",
            "billsNayVotes",
        )
        model = m.Rep
        load_instance = True

    id = ma.auto_field()
    affiliation = ma.auto_field("political_party", dump_only=True)
    capitolPhoneNumber = ma.auto_field("capitol_phone", dump_only=True)
    districtPhoneNumber = ma.auto_field("district_phone", dump_only=True)
    twitterUrl = ma.auto_field("twitter")
    billsSponsored = fields.Method("get_bills_sponsored", dump_only=True)
    billsYeaVotes = fields.Method("get_bills_yea_votes", dump_only=True)
    billsNayVotes = fields.Method("get_bills_nay_votes", dump_only=True)

    def get_bills_sponsored(self, rep):
        mapping = self.context.get("mapping")
        return mapping["sponsorship"]

    def get_bills_yea_votes(self, rep):
        mapping = self.context.get("mapping")
        return mapping["yea_vote"]

    def get_bills_nay_votes(self, rep):
        mapping = self.context.get("mapping")
        return mapping["nay_vote"]


class RepsResource(Resource):
    def get(self, search_query):
        search_query = "%{}%".format(search_query)
        conditions = [column.like(f'%{search_query}%') for column in [m.Rep.name, m.Rep.state, m.Rep.district, m.Rep.role]]
        query = db.session.query(m.Rep).filter(or_(*conditions))
        reps = query.all()[:100]

        bill_types = ["sponsorship", "yea_vote", "nay_vote"]
        result = []
        for rep in reps:
            negative_mapping = defaultdict(list)
            for bill_type in bill_types:
                bill_ids = db.session.query(m.RepsToNegativeBills).filter(and_(m.RepsToNegativeBills.rep_id == rep.id, m.RepsToNegativeBills.relation_type == bill_type)).all()
                for bill_id in bill_ids:
                    negative_bill = db.session.query(m.NegativeBills).filter(m.NegativeBills.id == bill_id.negative_bills_id).first()
                    negative_mapping[bill_type].append(negative_bill.case_name)

            reps_schema = RepSchema(context={'mapping': negative_mapping})
            result.append(reps_schema.dump(rep))

        try:
            return result
        except ValidationError as err:
            return err.messages, 422


api.add_resource(RepsResource, '/api/reps/search/<string:search_query>')


@app.cli.command("import-airtable-json")
@click.option("--state-reps-file", type=click.File('rb'), required=True)
@click.option("--national-reps-file", type=click.File('rb'), required=True)
@click.option("--negative-bills-file", type=click.File('rb'), required=True)
def import_airtable_json(state_reps_file, national_reps_file, negative_bills_file):
    state_reps = json.load(state_reps_file)
    m.Rep().bulk_upsert(db.session, state_reps)

    negative_bills = json.load(negative_bills_file)
    m.NegativeBills().bulk_upsert(db.session, negative_bills)

    m.RepsToNegativeBills.rep_build_all_relations(at_reps=state_reps, session=db.session)

if __name__ == '__main__':
    app.run(debug=True)
