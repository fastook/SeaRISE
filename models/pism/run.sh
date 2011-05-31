#!/bin/bash

# Copyright (C) 2009-2011 Andy Aschwanden

# PISM SeaRISE Greenland
#
#
# before using this script, run preprocess.sh to download and adjust metadata
# on SeaRISE "Present Day Greenland" master dataset
#
# recommended way to run with N processors is " ./run.sh N {1,2} 2>&1 | tee run.eo "
# which gives a viewable (with "less", for example) transcript in run.eo
#
# 
#
#

if [ -n "${SCRIPTNAME:+1}" ] ; then
  echo "[SCRIPTNAME=$SCRIPTNAME (already set)]"
  echo ""
else
  SCRIPTNAME="#(run.sh)"
fi

echo
echo "# =============================================================================="
echo "# PISM SeaRISE Greenland: Bedrock highres runs"
echo "# =============================================================================="
echo

set -e  # exit on error

NN=2  # default number of processors
if [ $# -gt 0 ] ; then  # if user says "cresis.sh 8" then NN = 8
  NN="$1"
fi

echo "$SCRIPTNAME              NN = $NN"
set -e  # exit on error

# set MPIDO if using different MPI execution command, for example:
#  $ export PISM_MPIDO="aprun -n "
if [ -n "${PISM_MPIDO:+1}" ] ; then  # check if env var is already set
  echo "$SCRIPTNAME      PISM_MPIDO = $PISM_MPIDO  (already set)"
else
  PISM_MPIDO="mpiexec -n "
  echo "$SCRIPTNAME      PISM_MPIDO = $PISM_MPIDO"
fi

# check if env var PISM_DO was set (i.e. PISM_DO=echo for a 'dry' run)
if [ -n "${PISM_DO:+1}" ] ; then  # check if env var DO is already set
  echo "$SCRIPTNAME         PISM_DO = $PISM_DO  (already set)"
else
  PISM_DO="" 
fi

# prefix to pism (not to executables)
if [ -n "${PISM_PREFIX:+1}" ] ; then  # check if env var is already set
  echo "$SCRIPTNAME     PISM_PREFIX = $PISM_PREFIX  (already set)"
else
  PISM_PREFIX=""    # just a guess
  echo "$SCRIPTNAME     PISM_PREFIX = $PISM_PREFIX"
fi

# set PISM_EXEC if using different executables, for example:
#  $ export PISM_EXEC="pismr -cold"
if [ -n "${PISM_EXEC:+1}" ] ; then  # check if env var is already set
  echo "$SCRIPTNAME       PISM_EXEC = $PISM_EXEC  (already set)"
else
  PISM_EXEC="pismr"
  echo "$SCRIPTNAME       PISM_EXEC = $PISM_EXEC"
fi

echo

# preprocess.sh generates pism_*.nc files; run it first
if [ -n "${PISM_DATANAME:+1}" ] ; then  # check if env var is already set
  echo "$SCRIPTNAME   PISM_DATANAME = $PISM_DATANAME  (already set)"
else
  PISM_BEDVER="1.1"
  PISM_DATANAME=pism_Greenland_5km_${BEDVER}.nc
fi


for INPUT in $PISM_DATANAME; do
  if [ -e "$INPUT" ] ; then  # check if file exist
    echo "$SCRIPTNAME           input   $INPUT (found)"
  else
    echo "$SCRIPTNAME           input   $INPUT (MISSING!!)"
    echo
    echo "$SCRIPTNAME           please run ./preprocess.sh, exiting"
    echo
    exit
  fi
done

INNAME=$PISM_DATANAME

# run lengths and starting time for paleo
SMOOTHRUNLENGTH=100
NOMASSSIARUNLENGTH=50000 # longer than searise, because we don't do paleo-climate spinup
COARSERUNLENGTH=25000
FINERUNLENGTH=5000

# grids
GRID10KM="-Mx 151 -My 281 -Lz 4000 -Lbz 2000 -Mz 51 -Mbz 26"
GRID5KM="-Mx 301 -My 561 -Lz 4000 -Lbz 2000 -Mz 51 -Mbz 26"

# grid spacings
GS10KM=10
GS5KM=5

# skips
SKIP10KM=50
SKIP5KM=200

# cat prefix and exec together
PISM="${PISM_PREFIX}${PISM_EXEC} -ocean_kill -e 3 -gradient mahaffy"

# coupler settings
COUPLER="-atmosphere searise_greenland -surface pdd -pdd_fausto"

# default choices in parameter study; see Bueler & Brown (2009) re "tillphi"
TILLPHI="-topg_to_phi 5.0,20.0,-300.0,700.0,10.0"

# use "control run" parameters from Bueler et al. submitted
PARAMS="-pseudo_plastic_q 0.25 -plastic_pwfrac 0.98 $TILLPHI"

# default is SIA
MODE="SIA"
FULLPYS=""

echo ""
if [ $# -gt 1 ] ; then
  if [ $2 -eq "1" ] ; then  # if user says "spinup.sh N 1" then SIA-only:
    echo "$SCRIPTNAME grid: ALL RUNS non-sliding SIA only"
    FULLPHYS=""
    MODE="SIA"
  fi
  if [ $2 -eq "2" ] ; then  # if user says "spinup.sh N 2" then SIA/SSA hybrid:
    echo "$SCRIPTNAME grid: ALL RUNS SIA/SSA hybrid"
    echo "$SCRIPTNAME       WARNING: VERY LARGE COMPUTATIONAL TIME"
    FULLPHYS="-ssa_sliding -thk_eff ${PARAMS}"
    MODE="SSA"
  fi
else
    echo "$SCRIPTNAME wrong choice (1: SIA, 2: SIA/SSA)"
fi
echo ""

echo "$SCRIPTNAME     coarse grid = '$GRID10KM' (= $GS10KM km)"
echo "$SCRIPTNAME       fine grid = '$GRID5KM' (= $GS5KM km)"


echo "$SCRIPTNAME      executable = '$PISM'"
echo "$SCRIPTNAME         tillphi = '$TILLPHI'"
echo "$SCRIPTNAME    full physics = '$FULLPHYS'"
echo "$SCRIPTNAME         coupler = '$COUPLER'"

GS=$GS10KM
GRID=$GRID10KM
SKIP=$SKIP10KM


# bootstrap and do smoothing run to $SMOOTHRUNLENGTH years
PRENAME=g${GS}km_${PISM_BEDVER}_pre${SMOOTHRUNLENGTH}.nc
echo
echo "$SCRIPTNAME  bootstrapping plus short smoothing run (for ${SMOOTHRUNLENGTH}a)"
cmd="$PISM_MPIDO $NN $PISM -skip $SKIP -boot_file $INNAME $GRID \
  $COUPLER -y ${SMOOTHRUNLENGTH} -o $PRENAME"
$PISM_DO $cmd


# run with -no_mass (no surface change) for 100ka
STEADYNAME=g${GS}km_${PISM_BEDVER}_steady.nc
EX1NAME=ex_${STEADYNAME}
EXTIMES=0:100:${NOMASSSIARUNLENGTH}
EXVARS="enthalpybase,temppabase,mask,bmelt,csurf,hardav,diffusivity" # add mask, so that check_stationarity.py ignores ice-free areas.
echo
echo "$SCRIPTNAME  -no_mass (no surface change) SIA run to achieve enthalpy equilibrium, for ${NOMASSSIARUNLENGTH}a"
cmd="$PISM_MPIDO $NN $PISM -skip $SKIP -i $PRENAME $COUPLER \
  -no_mass -y ${NOMASSSIARUNLENGTH} \
  -extra_file $EX1NAME -extra_vars $EXVARS -extra_times $EXTIMES -o $STEADYNAME"
$PISM_DO $cmd

# bootstrap and do smoothing run to $SMOOTHRUNLENGTH years
POSTNAME=g${GS}km_${PISM_BEDVER}_post${SMOOTHRUNLENGTH}.nc
echo
echo "$SCRIPTNAME smoothing run (for ${SMOOTHRUNLENGTH}a)"
cmd="$PISM_MPIDO $NN $PISM -skip $SKIP -i $STEADYNAME \
  $COUPLER -y ${SMOOTHRUNLENGTH} -o $POSTNAME"
$PISM_DO $cmd


# pre-spinup done;

EXSTEP=500
TSSTEP=1

STARTYEAR=0
ENDTIME=$(($STARTYEAR + $COARSERUNLENGTH))
REGRIDNAME=$POSTNAME

EXVARS="ftt_modified_acab,csurf,bmelt,diffusivity,hardav,thk,taud"
EXSTEP=5
EXTIMES=$STARTYEAR:$EXSTEP:$ENDTIME
OUTNAME=g${GS}km_${PISM_BEDVER}_${MODE}.nc
TSNAME=ts_$OUTNAME
TSTIMES=$STARTTIME:$TSSTEP:$ENDTIME
EXNAME=ex_$OUTNAME
EXTIMES=$STARTTIME:$EXSTEP:$ENDTIME
echo
echo "$SCRIPTNAME: ${GS}km grid"
cmd="$PISM_MPIDO $NN $PISM -skip $SKIP -boot_file $INNAME $GRID \
     $COUPLER $FULLPHYS \
     -regrid_file $REGRIDNAME -regrid_vars enthalpy,thk,litho_temp,bwat,bmelt \
     -ts_file $TSNAME -ts_times $STARTYEAR:1:$RUNLENGTH \
     -extra_file $EXNAME -extra_vars $EXVARS -extra_times $EXTIMES \
     -ys $STARTYEAR -y $RUNLENGTH -o $OUTNAME"
$PISM_DO $cmd


GS=$GS5KM
GRID=$GRID5KM
SKIP=$SKIP5KM


STARTYEAR=$ENDTIME
ENDTIME=$(($STARTYEAR + $FINERUNLENGTH))
REGRIDNAME=$OUTNAME
OUTNAME=g${GS}km_${PISM_BEDVER}_${MODE}.nc
TSTIMES=$STARTTIME:$TSSTEP:$ENDTIME
EXNAME=ex_$OUTNAME
EXTIMES=$STARTTIME:$EXSTEP:$ENDTIME
echo
echo "$SCRIPTNAME: ${GS}km grid"
cmd="$PISM_MPIDO $NN $PISM -skip $SKIP -boot_file $INNAME $GRID \
      -regrid_file $REGRIDNAME -regrid_vars enthalpy,thk,litho_temp,bwat,bmelt \
      $FULLPHYS $COUPLER \
     -ts_file $TSNAME -ts_times $STARTYEAR:1:$RUNLENGTH \
     -extra_file $EXNAME -extra_vars $EXVARS -extra_times $EXTIMES \
     -ys $STARTYEAR -y $RUNLENGTH -o $OUTNAME"
$PISM_DO $cmd


echo
echo "$SCRIPTNAME done"
