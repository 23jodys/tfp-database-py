from typing import List
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


class Base(DeclarativeBase):
    pass


class Rep(Base):
    __tablename__ = "reps"

    id: Mapped[str] = mapped_column(primary_key=True)
    # required fields
    name: Mapped[str]
    district: Mapped[str]
    role: Mapped[str]
    state: Mapped[str]

    # timestamps
    created: Mapped[str]
    modified: Mapped[str]

    political_party: Mapped[Optional[str]]
    reelection_date: Mapped[Optional[str]]
    website: Mapped[Optional[str]]

    # contact info
    email: Mapped[Optional[str]]
    facebook: Mapped[Optional[str]]
    twitter: Mapped[Optional[str]]
    capitol_address: Mapped[Optional[str]]
    capitol_phone: Mapped[Optional[str]]
    district_address: Mapped[Optional[str]]
    district_phone: Mapped[Optional[str]]

    # follow the money and legiscan
    ftm_eid: Mapped[Optional[int]]
    legiscan_id: Mapped[Optional[int]]

    def from_airtable_record(self, at_rep):
        self.id = at_rep["id"]
        self.name = at_rep["fields"]["Name"]
        self.district = at_rep["fields"]["District"]
        self.state = at_rep["fields"]["State"]
        self.role = at_rep["fields"]["Role"]
        self.created = at_rep["fields"]["Created"]
        self.modified = at_rep["fields"]["Last Modified"]

        self.political_party = at_rep.get("fields").get("Political Party")
        self.reelection_date = at_rep.get("fields").get("Up For Reelection On")
        self.website = at_rep.get("fields").get("Website")
        self.email = at_rep.get("fields").get("Email")
        self.facebook = at_rep.get("fields").get("Facebook")
        self.twitter = at_rep.get("fields").get("Twitter")
        self.capitol_address = at_rep.get("fields").get("Capitol Address")
        self.capitol_phone = at_rep.get("fields").get("Capitol Phone Number")
        self.district_address = at_rep.get("fields").get("District Address")
        self.district_phone = at_rep.get("fields").get("District Phone Number")
        self.ftm_eid = at_rep.get("fields").get("Follow the Money EID")
        self.legiscan_id = at_rep.get("fields").get("Legiscan ID")

        return self

    def to_dict(self):
        return dict((col, getattr(self, col)) for col in self.__table__.columns.keys())


rep_json_example = """{'createdTime': '2023-03-29T22:00:53.000Z',
  'fields': {'Capitol Address': '24 Beacon St., Room 166, Boston, MA 02133',
             'Capitol Phone Number': '(617) 722-2692',
             'Created': '2023-03-29T22:00:53.000Z',
             'District': '6th Norfolk',
             'Email': 'William.Galvin@mahouse.gov',
             'Facebook': 'https://www.facebook.com/profile.php?id=100057703163724',
             'Follow the Money EID': 839710,
             'Last Modified': '2023-07-11T22:15:31.000Z',
             'Legiscan ID': 2441,
             'Name': 'William Galvin',
             'Political Party': 'Democrat',
             'Role': 'House Representative',
             'State': 'Massachusetts',
             'Up For Reelection On': '2022-11-05',
             'Website': 'https://malegislature.gov/Legislators/Profile/WCG1'},
  'id': 'rec02eJ7tvAv6H8LX'}"""


class NegativeBills(Base):
    __tablename__ = "negative_bills"
    id: Mapped[str] = mapped_column(primary_key=True)

    bill_information_link: Mapped[Optional[str]]
    case_name: Mapped[str]

    # TODO figure out whether this should be a json field
    category: Mapped[Optional[str]]
    expanded_category: Mapped[Optional[str]]
    created: Mapped[str]
    last_activity: Mapped[Optional[str]]
    last_modified: Mapped[Optional[str]]
    legiscan_id: Mapped[Optional[int]]
    progress: Mapped[Optional[str]]
    state: Mapped[str]
    status: Mapped[Optional[str]]
    summary: Mapped[Optional[str]]

    def to_dict(self):
        return dict((col, getattr(self, col)) for col in self.__table__.columns.keys())


negative_bills_json_example = """{'createdTime': '2023-04-11T23:16:25.000Z',
  'fields': {'Bill Information Link': 'https://legiscan.com/AL/bill/HB261/2023',
             'Case Name': 'AL HB261',
             'Category': ['Sports'],
             'Created': '2023-04-11T23:16:25.000Z',
             'Expanded Category': ['Sports'],
             'Last Activity Date': '2023-05-24',
             'Last Modified': '2023-09-25T20:56:30.000Z',
             'Legiscan Bill ID': 1753574,
             'Nay Votes': ['rec07tcDNbZB0V9Uq',
                           'recTly9LNN7KVg19B',
                           'recC8BwAbWZV7EpPJ',
                           'recDzxdwSVTtQlL82',
                           'rec6eVWRueAqzFsmw',
                           'recktFndwtWb991Mc',
                           'recIgprrXIoyvf8eK',
                           'recPbuM6HqRZ2483j'],
             'Progress': 'Passed',
             'Sponsors': ['recdlZiMsonXtuWS7'],
             'State': 'Alabama',
             'Status': 'Passed',
             'Summary': 'This bill expands existing legislation in Alabama '
                        'that restricts sports participation for trans '
                        'students in K-12 schools to include public 2- and 4- '
                        'year colleges and universities. The bill claims '
                        'various advantages to those who were assigned male at '
                        'birth. The bill prohibits someone the state claims to '
                        'be a "biological male" from joining a sports team for '
                        '"females," and vice versa. The bill prohibits '
                        'complaints to be filed about restrictions to K-12, '
                        'college, and/or university sports teams, or '
                        'retaliation towards anyone who files complaints. The '
                        'bill additionally provides recourse for complaints, '
                        'such as going to court for injunctive relief, '
                        'damages, and/or fees.',
             'Yea Votes': ['recLLmtQiKSgBr31n',
                            ...
                           'recfClzN6s7UUAIHF']},
  'id': 'rec03K3y0yLY6M31u'}"""
