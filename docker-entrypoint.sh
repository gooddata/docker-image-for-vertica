#!/usr/bin/env bash

#
# (C) 2021 GoodData Corporation
#

if [ "${DEBUG_FAILING_STARTUP}" != "y" ]; then
  # Stop container, if any error occurs during startup
  # Can be overriden by setting DEBUG_FAILING_STARTUP to "y"
  set -e
fi

# We have to export it here, vertica_env.sh is not propagated into entrypoint script
export VERTICA_DB_USER="`whoami`"
STOP_LOOP="false"
VSQL="${VERTICA_OPT_DIR}/bin/vsql -U ${VERTICA_DB_USER}"
ADMINTOOLS="${VERTICA_OPT_DIR}/bin/admintools"

# Vertica should be shut down properly
function shut_down() {
  echo "Shutting Down"
  vertica_proper_shutdown
  echo 'Stopping loop'
  STOP_LOOP="true"
}

function vertica_proper_shutdown() {
  echo 'Vertica: Closing active sessions'
  ${VSQL} -c 'SELECT CLOSE_ALL_SESSIONS();'
  echo 'Vertica: Flushing everything on disk'
  ${VSQL} -c 'SELECT MAKE_AHM_NOW();'
  echo 'Vertica: Stopping database'
  ${ADMINTOOLS} -t stop_db -d $VERTICA_DB_NAME -i
}

function create_app_db_user() {
  echo ''
  echo "Creating APP DB user ${APP_DB_USER} ... "
  CHECK_STRING="ALREADY_EXISTS"
  CHECK_QUERY="select case when count(*) > 0 then '${CHECK_STRING}' end from users where user_name = '${APP_DB_USER}'"
  ALREADY_EXISTS=$($VSQL -c "${CHECK_QUERY}" | grep ${CHECK_STRING} | sed 's/ //g' || true)
  if [ "${ALREADY_EXISTS}" != "${CHECK_STRING}" ]; then
    ${VSQL} -c "create user ${APP_DB_USER}"
    ${VSQL} -c "grant pseudosuperuser to ${APP_DB_USER}"
    ${VSQL} -c "alter user ${APP_DB_USER} default role all"
  fi
  # Alter the user password everytime to support change of the password
  # We must prevent error "ROLLBACK 2301:  Can not reuse current password" with " || true"
  ${VSQL} -c "alter user ${APP_DB_USER} identified by '${APP_DB_PASSWORD}'" || true
}

trap "shut_down" SIGKILL SIGTERM SIGHUP SIGINT

if [ -n "${TZ}" ]; then
  echo "Custom time zone required - ${TZ}"
  if [ ! -f "${VERTICA_OPT_DIR}/share/timezone/${TZ}" ]; then
    echo "ERROR: timezone file ${VERTICA_OPT_DIR}/${TZ} does not exist"
    echo "Check Dockerfile and uncomment a workaround solution linking system time zones"
    exit 1
  fi
fi

echo 'Starting up'
if [ -z "$(ls -A "${VERTICA_DATA_DIR}")" ]; then
  echo 'Creating database'
  ${ADMINTOOLS} -t create_db --skip-fs-checks -s localhost -d $VERTICA_DB_NAME -c ${VERTICA_DATA_DIR} -D ${VERTICA_DATA_DIR}
  echo
  echo "Persisting admintools.conf into ${VERTICA_DATA_DIR} ..."
  mkdir -p ${VERTICA_DATA_DIR}/config
  /bin/mv ${VERTICA_OPT_DIR}/config/admintools.conf ${VERTICA_DATA_DIR}/config/admintools.conf
  /bin/ln -s ${VERTICA_DATA_DIR}/config/admintools.conf ${VERTICA_OPT_DIR}/config/admintools.conf
else
  echo 'Starting Database'
  ${ADMINTOOLS} -t start_db -d $VERTICA_DB_NAME -i
fi

echo
echo 'Loading VMart schema ...'
if [ "${VMART_LOAD_DATA}" == "y" ]; then
  ${VMART_DIR}/${VMART_ETL_SCRIPT}
else
  echo "Nothing to load, VMART_LOAD_DATA=$VMART_LOAD_DATA"
fi

echo
if [ -d /docker-entrypoint-initdb.d/ ]; then
  echo "Running entrypoint scripts ..."
  for f in $(ls /docker-entrypoint-initdb.d/* | sort); do
    case "$f" in
      *.sh)     echo "$0: running $f"; . "$f" ;;
      *.sql)    echo "$0: running $f"; ${VSQL} -f $f; echo ;;
      *)        echo "$0: ignoring $f" ;;
    esac
   echo
  done
fi

if [ -n "${APP_DB_USER}" ]; then
  create_app_db_user
fi

echo
echo "Vertica is now running"

while [ "${STOP_LOOP}" == "false" ]; do
  sleep 1
done
