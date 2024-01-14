#!/bin/bash

set -o pipefail
set -e
set -x

# Populate schema
flask --app "tfp_widget:create_app('production')" db upgrade

# Fetch airtable
rm -f state_reps*.json national_reps*.json negative_bills*.json
python dump_airtable.py

# Import airtable
flask --app "tfp_widget:create_app('production')" import-airtable-json \
  --state-reps-file state_reps*.json \
  --national-reps-file national_reps*.json \
  --negative-bills-file negative_bills*.json \
  --build-rep-nb-relations