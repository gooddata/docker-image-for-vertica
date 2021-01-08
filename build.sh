#!/usr/bin/env bash

#
# (C) 2021 GoodData Corporation
#

set -e

function show_help() {
  cat << EOF
Usage: $0 -v <vertica version> -f <OS family> -o <OS version> [-r <docker repository>]
Options are:
  -v - Vertica version, e.g. 10.0.1-5
  -f - OS family, e.g. CentOS, Debian
  -o - OS version of base image, e.g. 7.9.2009, 8.3.2011, ubuntu:18.04
  -r - Image name prefix, a path to repository, e.g. 123456789012.dkr.ecr.eu-central-1.amazonaws.com/databases
  -p - Push built image into repository defined by the image name prefix (-r)
  -h - show help
EOF
}

function report_invalid_arg() {
   echo "Missing mandatory $1 option"
   echo
   show_help
}

# A POSIX variable
OPTIND=1 # Reset in case getopts has been used previously in the shell.

REPOSITORY=""
VERTICA_VERSION=""
OS_FAMILY=""
OS_VERSION=""
VERTICA_IMAGE=""
PUSH_IMAGE="n"

while getopts "h?v:f:o:r:p" opt; do
    case "$opt" in
    h)  show_help
        exit 0
        ;;
    \?) echo "Invalid option: -$OPTARG" >&2
        echo
        show_help
        exit 1
        ;;
    v)  VERTICA_VERSION="${OPTARG}"
        ;;
    f)  OS_FAMILY="${OPTARG}"
        ;;
    o)  OS_VERSION="${OPTARG}"
        ;;
    r)  REPOSITORY="${OPTARG}"
        ;;
    p)  PUSH_IMAGE="y"
        ;;
    esac
done

shift $((OPTIND-1))

if [ -z "${VERTICA_VERSION}" ]; then
  report_invalid_arg "-v"
  exit 1
fi

if [ -z "${OS_VERSION}" ]; then
  report_invalid_arg "-o"
  exit 1
fi

if ! ls packages/vertica?${VERTICA_VERSION}* 1>/dev/null 2>&1; then
  echo "No Vertica package file exists in \"packages\" folder for Vertica version ${VERTICA_VERSION}"
  exit 1
fi

IMAGE_VERSION=$(echo "${VERTICA_VERSION}.${OS_FAMILY}_${OS_VERSION}" | sed -r 's/[^a-z0-9_.-]/_/gi')

if [ -z "${REPOSITORY}" ]; then
  VERTICA_IMAGE="vertica:${IMAGE_VERSION}"
else
  VERTICA_IMAGE="${REPOSITORY}/vertica:${IMAGE_VERSION}"
fi

echo "Building image $VERTICA_IMAGE ...."
docker build -f Dockerfile_${OS_FAMILY} \
  --build-arg vertica_version=${VERTICA_VERSION} \
  --build-arg os_version=${OS_VERSION} \
  -t $VERTICA_IMAGE .

if [ "${PUSH_IMAGE}" == "y" ]; then
  echo "Pushing $VERTICA_IMAGE to repository ...."
  docker push $VERTICA_IMAGE
fi
