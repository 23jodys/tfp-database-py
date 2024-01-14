import json
import logging

import click
from flask.cli import with_appcontext

from . import models
from .database import db


@click.command("import-airtable-json")
@click.option("--state-reps-file", type=click.File('rb'),
              help="File containing state reps from dump_airtable", required=True)
@click.option("--national-reps-file", type=click.File('rb'),
              help="File containing national reps dump_airtable")
@click.option("--negative-bills-file", type=click.File('rb'),
              help="CSV file with negative bills dump_airtable")
@click.option("--build-rep-nb-relations", is_flag=True, default=True,
              help="Build relationship table between reps and negative-bills")
@with_appcontext
def import_airtable_json(state_reps_file, national_reps_file, negative_bills_file, build_rep_nb_relations):
    logger = logging.getLogger()
    state_reps = None
    if state_reps_file:
        state_reps = json.load(state_reps_file)
        models.Rep.bulk_upsert(state_reps)
    logger.info(f"Updated {len(state_reps)} State Reps")

    negative_bills = None
    if negative_bills_file:
        negative_bills = json.load(negative_bills_file)
        models.NegativeBills.bulk_upsert(negative_bills)
    logger.info(f"Updated {len(negative_bills)} Negative Bills")

    if national_reps_file:
        # do nothing, haven't implemented this yet
        pass

    if build_rep_nb_relations:
        models.RepsToNegativeBills.rep_build_all_relations(at_reps=state_reps, session=db.session)
