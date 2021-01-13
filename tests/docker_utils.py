#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (C) 2021 GoodData Corporation

from tests.cmd_utils import exec_cmd
from time import time


def build_vertica_image(os_family, vertica_setup, os_version, vertica_version, vertica_tag):
    print("Building Vertica docker image - " +
          f" {os_family['name']} :: {os_version} :: {vertica_version}, TAG={vertica_tag}")
    docker_cmd = f"""
                docker build -q -f Dockerfile_{os_family['name']} \\
                    --build-arg vertica_version={vertica_version} \\
                    --build-arg os_version={os_version} \\
                    --build-arg vertica_db_user={vertica_setup['db_user']} \\
                    --build-arg vertica_db_group={vertica_setup['db_group']} \\
                    --build-arg vertica_db_name={vertica_setup['db_name']} \\
                    --build-arg vmart_start_year={vertica_setup['vmart_start_year']} \\
                    --build-arg vmart_end_year={vertica_setup['vmart_end_year']} \\
                    --build-arg remove_packages='{vertica_setup['remove_packages']}' \\
                    -t {vertica_tag} .
            """
    exec_docker_command(docker_cmd)


def run_vertica_container(vertica_setup, vertica_container_name, vertica_tag, load_data):
    vmart_load_data = 'y' if load_data else 'n'

    docker_cmd = f"""
            docker run -d -p {vertica_setup['exposed_port']}:5433 \\
                       --name {vertica_container_name} \\
                       -e TZ='{vertica_setup['time_zone']}' \\
                       -e APP_DB_USER='{vertica_setup['app_db_user']}' \\
                       -e APP_DB_PASSWORD='{vertica_setup['app_db_password']}' \\
                       -e VMART_LOAD_DATA={vmart_load_data} \\
                       --rm \\
                       {vertica_tag}
            """
    exec_docker_command(docker_cmd)


def stop_docker_container(vertica_container_name):
    docker_cmd = f"""
            docker stop {vertica_container_name}
            """
    exec_docker_command(docker_cmd)


def exec_docker_command(docker_cmd):
    print(docker_cmd)
    start = time()
    result = exec_cmd(docker_cmd)
    print(f'RESULT: {result}')
    duration = int((time() - start) * 1000)
    print(f"Command finished successfully time={duration}")
