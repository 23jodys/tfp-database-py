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


json_example = """{'createdTime': '2023-03-29T22:00:53.000Z',
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
