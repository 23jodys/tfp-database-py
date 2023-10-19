# required token for authentication to airtable database
AIRTABLE_API_TOKEN="token"

# This value can be found off the API documentation site:
# https://airtable.com/appVXvrTCBaSvn2Id/api/docs
# id string of the database
AIRTABLE_BASE='baseid'

# a basic testing flag
# TESTING : use testing environment and database
# INTEGRATION_TESTING : testing using live servers and apis
# PRODUCTION : use production environment and database
RUN_ENV='TESTING'

# in-memory sqlite
TEST_MEM='sqlite::memory:'

# These values can be found off the API documentation site:
# https://airtable.com/appVXvrTCBaSvn2Id/api/docs

STATE_REPS_TABLE="tbl..."
NEGATIVE_BILLS_TABLE="tbl..."
POSITIVE_BILLS_TABLE="tbl..."
NATIONAL_BILLS_TABLE="tbl..."
NATIONAL_REPS_TABLE="tbl..."

