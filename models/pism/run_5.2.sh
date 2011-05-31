#!/bin/bash

# runs PISM on DEVELOPMENTAL SeaRISE "Present Day Greenland" master dataset

set -e  # exit on error

# run  preprocess.sh first

export PISM_DATANAME=pism_Greenland_5km_v5.2_JakHelKan.nc
export PISM_BEDVER="5.2"
export SCRIPTNAME="#(run_5.2.sh)"

./run.sh $1 $2


