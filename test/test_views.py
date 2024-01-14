import json

from tfp_widget.database import db
from tfp_widget.models import Rep, NegativeBills, RepsToNegativeBills

negative_rep_example = {"id": "recaMS906YE9Kq2bj", "createdTime": "2021-10-20T15:36:50.000Z", "fields": {
"Name": "Tim Barhorst",
"Political Party": "Republican",
"District": "85",
"Role": "House Representative",
"State": "Ohio",
"Email": "rep85@ohiohouse.gov",
"Capitol Phone Number": "(614) 466-1507",
"Website": "https://ohiohouse.gov/members/tim-barhorst",
"Capitol Address": "77 S. High Street, Floor 11, Columbus, OH 43215",
"Facebook": "https://www.facebook.com/TimBarhorst",
"Twitter": "https://twitter.com/timbarhorst",
"Up For Reelection On": "2024-11-05",
"Sponsorships": [
  "recs99WthsQVu2BUe",
],
"Yea Votes": [
  "recs99WthsQVu2BUe",
],
"Nay Votes": [
],
"Legiscan ID": 24456,
"Follow the Money EID": 55796704,
"Last Modified": "2023-12-01T18:49:00.000Z",
"Created": "2021-10-20T15:36:50.000Z"}}

negative_bill_example = json.loads("""\
{
  "id": "recs99WthsQVu2BUe",
  "createdTime": "2023-03-07T18:17:13.000Z",
  "fields": {
    "Case Name": "OH HB68",
    "Status": "Active",
    "Progress": "Veto Override Vote",
    "Summary": "This bill mandates that no health care professional ...",
    "State": "Ohio",
    "Bill Information Link": "https://legiscan.com/OH/bill/HB68/2023",
    "Last Activity Date": "2024-01-10",
    "Sponsors": [
      "recaMS906YE9Kq2bj"
    ],
    "Yea Votes": [
      "recaMS906YE9Kq2bj"
    ],
    "Nay Votes": [
    ],
    "Category": [
      "Health Care",
      "Sports"
    ],
    "Legiscan Bill ID": 1723919,
    "Expanded Category": [
      "Healthcare Ban",
      "Sports"
    ],
    "Last Modified": "2024-01-04T19:50:22.000Z",
    "Created": "2023-03-07T18:17:13.000Z"
  }
}
""")


def test_no_query(client):
    response = client.get('/api/reps/search/')
    assert response.status_code == 404

def test_basic_rep(client):
    new_rep = Rep.from_airtable_record(negative_rep_example)
    db.session.add(new_rep)

    new_bill = NegativeBills.from_airtable_record(negative_bill_example)
    db.session.add(new_bill)

    RepsToNegativeBills.rep_build_all_relations([negative_rep_example], db.session)

    response = client.get('/api/reps/search/barhorst')
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]["name"] == "Tim Barhorst"


