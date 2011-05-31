#!/bin/bash

# runs PISM on DEVELOPMENTAL SeaRISE "Present Day Greenland" master dataset

set -e  # exit on error

# run  preprocess.sh first

PISM_BEDVER="0.93"
SRGDEV_NAME=Greenland_5km_v${PISM_BEDVER}.nc
export PISM_DATANAME=pism_$SRGDEV_NAME
export PISM_BEDVER="0.93"
export SCRIPTNAME="#(run_0.93.sh)"

./run.sh $1 $2


