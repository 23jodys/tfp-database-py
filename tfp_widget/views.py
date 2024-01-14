from sqlalchemy import or_, and_
from collections import defaultdict
from flask_restful import Resource
from marshmallow import ValidationError
from . import models as m
from . import schema


# noinspection PyMethodMayBeStatic
class RepsResource(Resource):
    def get(self, search_query):
        search_query = "%{}%".format(search_query)
        conditions = [column.ilike(f'%{search_query}%') for column in
                      [m.Rep.name, m.Rep.state, m.Rep.district, m.Rep.role]]
        query = m.Rep.query.filter(or_(*conditions))
        reps = query.all()[:100]

        bill_types = ["sponsorship", "yea_vote", "nay_vote"]
        result = []
        for rep in reps:
            negative_mapping = defaultdict(list)
            for bill_type in bill_types:
                bill_ids = m.RepsToNegativeBills.query.filter(
                    and_(m.RepsToNegativeBills.rep_id == rep.id,
                         m.RepsToNegativeBills.relation_type == bill_type)).all()
                for bill_id in bill_ids:
                    negative_bill = m.NegativeBills.query.filter(
                        m.NegativeBills.id == bill_id.negative_bills_id).first()
                    negative_mapping[bill_type].append(negative_bill.case_name)

            reps_schema = schema.RepSchema(context={'mapping': negative_mapping})
            result.append(reps_schema.dump(rep))

        try:
            return result
        except ValidationError as err:
            return err.messages, 422
