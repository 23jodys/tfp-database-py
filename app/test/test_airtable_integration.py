import os
import pytest
import app.AirTable.tfp_air_table as Airtable

INTEGRATION_TEST = os.getenv("RUN_ENV") == "INTEGRATION_TESTING"
AIRTABLE_API_TOKEN = os.getenv("AIRTABLE_API_TOKEN")
AIRTABLE_BASE = os.getenv("AIRTABLE_BASE")

AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE}"


def test_get_state_reps():
    if not INTEGRATION_TEST:
        pytest.skip("Skipping Airtable API calls.")

    reps = Airtable.get_state_reps(AIRTABLE_URL, AIRTABLE_API_TOKEN)
    assert len(reps) > 1000

    sample_rep = reps[0]
    assert "Name" in sample_rep["fields"]
    assert len(sample_rep["fields"]["Name"]) > 0
