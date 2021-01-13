#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (C) 2021 GoodData Corporation

import yaml
import re
import argparse
import time
from tests.docker_utils import build_vertica_image, run_vertica_container, stop_docker_container
import tests.vertica_tests as vtests

vertica_container_name = 'vertica_docker_test_db'
vertica_repo = 'vertica'

parser = argparse.ArgumentParser(
    conflict_handler="resolve",
    description="Run integration tests against Vertica databases.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument(
    '-h', '--host', default='localhost',
    help='Hostname of Vertica databases to be tested, running in container, default=localhost')
parser.add_argument(
    '-l', '--load-data', action='store_true', default=False,
    help='Trigger generation and load of VMART schema')
parser.add_argument(
    '-c', '--config-file', default='tests/config.yaml',
    help='Path to config file containing configuration of tests to be executed')


args = parser.parse_args()

with open(args.config_file) as fp:
    config = yaml.safe_load(fp)

vertica_setup = config['vertica_setup']


def run_tests():
    vtests.test_db_up(args.host, vertica_setup, vertica_container_name)
    vtests.test_vertica_version(args.host, vertica_setup, vertica_version)
    vtests.test_app_user(args.host, vertica_setup)
    vtests.test_os_user(vertica_container_name, vertica_setup)
    vtests.test_timezone(args.host, vertica_setup)
    vtests.test_remove_packages(args.host, vertica_setup)
    if args.load_data:
        vtests.test_vmart_load(args.host, vertica_setup)


tag_re = re.compile('[^a-z0-9_.-]', re.I)
start = time.time()
for os_family in config['os_families']:
    print(os_family['name'])
    for os_version in os_family['os_versions']:
        for vertica_version in config['vertica_versions']:
            tmp_vertica_tag = f"{vertica_version}.{os_family['name']}_{os_version}"
            vertica_tag = f"{vertica_repo}:{tag_re.sub('_', tmp_vertica_tag)}"
            build_vertica_image(os_family, vertica_setup, os_version, vertica_version, vertica_tag)
            try:
                run_vertica_container(vertica_setup, vertica_container_name, vertica_tag, args.load_data)
                run_tests()
            finally:
                stop_docker_container(vertica_container_name)
duration = int((time.time()-start)*1000)
print('')
print(f'TESTS finished duration={duration}')
