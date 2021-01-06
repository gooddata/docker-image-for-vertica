#!/bin/bash

VSQL="${VERTICA_OPT_DIR}/bin/vsql -U $VERTICA_DB_USER"

LOAD_CHECK_STRING="ALREADY_LOADED"
LOAD_CHECK_QUERY="select case when count(*) > 0 then '${LOAD_CHECK_STRING}' end from tables
  where table_schema = '${VMART_CONFIRM_LOAD_SCHEMA}' and table_name = '${VMART_CONFIRM_LOAD_TABLE}'"
ALREADY_LOADED=$($VSQL -c "${LOAD_CHECK_QUERY}" | grep ${LOAD_CHECK_STRING} | sed 's/ //g' || true)

if [ "${ALREADY_LOADED}" != "${LOAD_CHECK_STRING}" ]; then

  echo "Dropping old schema ..."
  cd ${VMART_DIR} && $VSQL -f vmart_schema_drop.sql

  VMART_END_YEAR=$((1 + $(date +%Y)))
  VMART_START_YEAR=$((${VMART_END_YEAR} - ${VMART_YEARS:-4}))

  echo "Generating data ..."
  cd ${VMART_DIR} && ./vmart_gen \
    --datadirectory ./ \
    --store_sales_fact 5000000 \
    --product_dimension 500 \
    --store_dimension 50 \
    --promotion_dimension 100 \
    --years "${VMART_START_YEAR}-${VMART_END_YEAR}" \
    --time_file Time_custom.txt

  echo "Creating schema ..."
  cd ${VMART_DIR} && $VSQL -f vmart_define_schema.sql

  echo "Loading files ..."
  cd ${VMART_DIR} && $VSQL -f vmart_load_data.sql

  echo "Running ETL ..."
  cd ${VMART_DIR} && $VSQL -f ${VMART_ETL_SQL}

  echo "Confirm successful load"
  $VSQL -c "create table if not exists ${VMART_CONFIRM_LOAD_SCHEMA}.${VMART_CONFIRM_LOAD_TABLE} (a int)"
else
  echo "Nothing to load, ALREADY_LOADED=${ALREADY_LOADED}"
fi
