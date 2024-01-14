from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, auto_field

from .models import Rep


class NegativeBillsSchema(SQLAlchemyAutoSchema):
    pass


# noinspection PyUnusedLocal
class RepSchema(SQLAlchemyAutoSchema):
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
        model = Rep
        load_instance = True

    id = auto_field()
    affiliation = auto_field("political_party", dump_only=True)
    capitolPhoneNumber = auto_field("capitol_phone", dump_only=True)
    districtPhoneNumber = auto_field("district_phone", dump_only=True)
    twitterUrl = auto_field("twitter")
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
