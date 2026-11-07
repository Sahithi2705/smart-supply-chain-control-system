"""Run Module 1 local canonical pipeline. Raw CSVs must first be extracted to data/raw."""
from profiling.profile_sources import main as profile_main
from transformations.etl_m5 import run_m5
from transformations.etl_olist import run_olist
from transformations.etl_scms import run_scms
from validation.validate_outputs import main as validate_main
from build_duckdb import main as duckdb_main

if __name__ == "__main__":
    profile_main()
    run_m5()
    run_olist()
    run_scms()
    validate_main()
    duckdb_main()
