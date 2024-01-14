from dotenv import load_dotenv
import os
from requests_ratelimiter import LimiterSession
import logging

logging.basicConfig(level=logging.INFO)


# The requests_ratelimiter library ensures we stay
# under the airtable rate limits (5 per second).
# Anything you use requests for to get information from
# airtable should go through this session object instead.
session = LimiterSession(per_second=5)

# Load environment variables from .env
load_dotenv()


def get_records_by_page(url, table_id, token, offset=None):
    """Get a single page of records from airtable. If offset is provided, this will
    return the page identified by the offset string.

    Args:
        url (string): URL to the airtable API endpoint, with the ID of the base/view appended.
        table_id (string): airtable table identifier. Probably looks like `tblcW1C6fiNHBnDaC`
        token (string): Authentication token for airtable API.
        offset (string, optional): Offset string provided by airtable in the previous page of data. Defaults to None.

    Returns:
        list: List of records translated to Python dicts.
    """
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


def get_table_data(table_key):
    """Get all records in an airtable table, repeatedly requesting page after page.

    Args:
        table_key (string): Environment variable *key* to look up the table id.

    Returns:
        list: List of records translated to Python dicts.
    """
    table_id = os.getenv(table_key)
    token = os.getenv("AIRTABLE_API_TOKEN")
    url = f"https://api.airtable.com/v0/{os.getenv('AIRTABLE_BASE')}"
    response = get_records_by_page(url, table_id, token)
    if response.status_code == 200:
        records = response.json()["records"]

        while "offset" in response.json():
            offset = response.json()["offset"]
            response = get_records_by_page(url, table_id, token, offset)
            more_records = response.json()["records"]
            records.extend(more_records)
            logging.info(f"{table_key} Records: {len(records)}")

        return records
    else:
        raise ConnectionError(f"Response code is not 200, got {response.status_code} and {response.data}")


def get_state_reps():
    """Convenience function to get all records from the State Reps table.

    Returns:
        list: List of records translated to Python dicts.
    """
    print("Fetching state reps table.")
    records = get_table_data("STATE_REPS_TABLE")
    return records


def get_national_reps():
    """Convenience function to get all records from the National Reps table.

    Returns:
        list: List of records translated to Python dicts.
    """
    print("Fetching state reps table.")
    records = get_table_data("NATIONAL_REPS_TABLE")
    return records


def get_negative_bills():
    """Convenience function to get all records from the State Reps table.

    Returns:
        list: List of records translated to Python dicts.
    """
    print("Fetching negative bills table.")
    records = get_table_data("NEGATIVE_BILLS_TABLE")
    return records
