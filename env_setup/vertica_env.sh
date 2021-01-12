#!/usr/bin/env bash

#
# (C) 2021 GoodData Corporation
#

#######################################################################################
# Set correct search PATH
export PATH="$PATH:${VERTICA_OPT_BIN}"

#######################################################################################
# Vertica variables and aliases
export VERTICA_DB_HOME="${VERTICA_DATA_DIR}/${VERTICA_DB_NAME}"
export VERTICA_CATALOG="${VERTICA_DB_HOME}/v_${VERTICA_DB_NAME}_*_catalog"
export VERTICA_DATA="${VERTICA_DB_HOME}/v_${VERTICA_DB_NAME}_*_data"
export VERTICA_DB_USER="`whoami`"

alias cdc="cd $VERTICA_CATALOG"
alias cdd="cd $VERTICA_DATA"

# Start / stop database (cluster)
#   be careful on multi-node cluster - it has to be executed under root using run_init
alias startdb="${VERTICA_OPT_BIN}/adminTools --tool start_db -d ${VERTICA_DB_NAME}"
alias stopdb="${VERTICA_OPT_BIN}/adminTools --tool stop_db -d ${VERTICA_DB_NAME}"

alias vsqlv="vsql -U ${VERTICA_DB_USER} -p 5433"

alias taillog="tail -f ${VERTICA_CATALOG}/vertica.log"
