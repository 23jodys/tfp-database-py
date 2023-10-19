from dotenv import load_dotenv
import requests
import os
from requests_ratelimiter import LimiterSession

session = LimiterSession(per_second=5)

load_dotenv()


def get_records_by_page(url, table_id, token, offset=None):
    """Add scores to the Airtable."""
    url = f"{url}/{table_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    params = {"pageSize": 100}

    if offset:
        params["offset"] = offset

    response = session.request("GET", url, headers=headers, params=params)

    return response


def get_state_reps(url, token):
    table_id = os.getenv("STATE_REPS_TABLE")
    response = get_records_by_page(url, table_id, token)
    if response.status_code == 200:
        reps = response.json()["records"]

        while "offset" in response.json():
            offset = response.json()["offset"]
            print(f"offset: {offset}")
            response = get_records_by_page(url, table_id, token, offset)
            more_reps = response.json()["records"]
            reps.extend(more_reps)
            print(f"State Reps: {len(reps)}")

        return reps
