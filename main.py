import os

from dotenv import load_dotenv
from flask import Flask, request
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource
from marshmallow import ValidationError, fields
from sqlalchemy import or_

from app.DataBase import models as m
from app.DataBase.models import RepsToNegativeBills

app = Flask(__name__)
CORS(app)

load_dotenv()

print(f"{os.getcwd()}")
print(f"{os.getenv('TEST_DB')}")

DB_URI = 'sqlite:///' + os.path.abspath(os.getcwd())  + "/test.db"

print(f"DB_URI: {DB_URI}")

app.config["SQLALCHEMY_DATABASE_URI"] = DB_URI

db = SQLAlchemy(model_class=m.Base)
db.init_app(app)

ma = Marshmallow(app)
api = Api(app)

class NegativeBillsSchema(ma.SQLAlchemyAutoSchema):
    pass

class RepSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        #fields = ("id", "name", "district", "role")
        model = m.Rep
        load_instance = True

    id = ma.auto_field()
    affiliation = ma.auto_field("political_party", dump_only=True)
    billsSponsored = fields.List(fields.Nested(NegativeBillsSchema()))


rep_schema = RepSchema()
reps_schema = RepSchema(many=True)


class RepsResource(Resource):
    def get(self, search_query):
        search_query = "%{}%".format(search_query)
        conditions = [column.like(f'%{search_query}%') for column in [m.Rep.name, m.Rep.state, m.Rep.district, m.Rep.role]]

        query = db.session.query(
            m.Rep,
            db.session.query(
                m.RepsToNegativeBills.negative_bills_id
            )
            .filter(RepsToNegativeBills.rep_id == m.Rep.id)
            .subquery(),
        ).group_by(m.Rep.id)



        #query = db.session.query(m.Rep, m.RepsToNegativeBills).join(m.RepsToNegativeBills, m.Rep.id == m.RepsToNegativeBills.rep_id)
        #query = db.session.query(m.RepsToNegativeBills).join(m.Rep).filter(or_(*conditions))
        print(query)
        reps = query.all()[:10]

        result = reps_schema.dump([x for x, y in reps])
        print(result)

        try:
            return reps_schema.dump(result)
        except ValidationError as err:
            return err.messages, 422


api.add_resource(RepsResource, '/api/reps/search/<string:search_query>')

if __name__ == '__main__':
    app.run(debug=True)
