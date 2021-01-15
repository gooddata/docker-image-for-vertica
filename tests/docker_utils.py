#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (C) 2021 GoodData Corporation

import re
import time

from tests.cmd_utils import exec_cmd
import tests.config as config


def build_vertica_image(os_family: str, vertica_setup: config.VerticaSetup, os_version: str,
                        vertica_version: str, vertica_tag: str):
    print("Building Vertica docker image - " +
          f" {os_family} :: {os_version} :: {vertica_version}, TAG={vertica_tag}")
    docker_cmd = f"""
                docker build -q -f Dockerfile_{os_family} \\
                    --build-arg vertica_version={vertica_version} \\
                    --build-arg os_version={os_version} \\
                    --build-arg vertica_db_user={vertica_setup.db_user} \\
                    --build-arg vertica_db_group={vertica_setup.db_group} \\
                    --build-arg vertica_db_name={vertica_setup.db_name} \\
                    --build-arg vmart_start_year={vertica_setup.vmart_start_year} \\
                    --build-arg vmart_end_year={vertica_setup.vmart_end_year} \\
                    --build-arg remove_packages='{vertica_setup.remove_packages}' \\
                    -t {vertica_tag} .
            """
    exec_docker_command(docker_cmd)


def run_vertica_container(vertica_setup: config.VerticaSetup, vertica_tag: str, volume_name: str, load_data: bool):
    vmart_load_data = 'y' if load_data else 'n'

    docker_cmd = f"""
            docker run -d -p {vertica_setup.exposed_port}:5433 \\
                       --name {vertica_setup.vertica_container_name} \\
                       --mount type=volume,source={volume_name},destination=/data \\
                       -e TZ='{vertica_setup.time_zone}' \\
                       -e APP_DB_USER='{vertica_setup.app_db_user}' \\
                       -e APP_DB_PASSWORD='{vertica_setup.app_db_password}' \\
                       -e VMART_LOAD_DATA={vmart_load_data} \\
                       --rm \\
                       {vertica_tag}
            """
    exec_docker_command(docker_cmd)


def stop_docker_container(vertica_setup: config.VerticaSetup):
    docker_cmd = f"""
            docker stop {vertica_setup.vertica_container_name}
            """
    exec_docker_command(docker_cmd)


def create_docker_volume(vertica_tag: str) -> str:
    volume_name = f"docker_vertica_image_test{re.sub(r'[:.-]', '_', vertica_tag)}_{int(time.time())}"
    docker_cmd = f"""
            docker volume create {volume_name}
            """
    exec_docker_command(docker_cmd)
    return volume_name


def is_docker_volume_in_use(volume_name: str):
    docker_cmd = f"""
            docker ps -aq -f "volume={volume_name}"
            """
    result = exec_docker_command(docker_cmd)
    return True if result.strip() else False


def remove_docker_volume(volume_name: str):
    retries = 5
    retries_count = 0
    while retries_count < retries and is_docker_volume_in_use(volume_name):
        retries_count += 1
        time.sleep(2)

    if retries_count >= retries:
        print(f"Volume {volume_name} still in use. Proceeding with volume delete anyway")

    docker_cmd = f"""
            docker volume rm -f {volume_name}
            """
    exec_docker_command(docker_cmd)


def exec_docker_command(docker_cmd) -> str:
    print(docker_cmd)
    start = time.time()
    result = exec_cmd(docker_cmd)
    duration = int((time.time() - start) * 1000)
    print(f"Command finished successfully time={duration}")
    return result


def poll_for_db_service(vertica_setup: config.VerticaSetup):
    service_address = f"{vertica_setup.host}:{vertica_setup.exposed_port}"
    print(f'Waiting on DB service {service_address}')
    sleep_delay = 2
    multiplier = 2
    max_threshold = 20

    while True:
        output = exec_cmd(f"docker logs --tail 1 {vertica_setup.vertica_container_name}").rstrip()
        if output == 'Vertica is now running':
            return

        time.sleep(sleep_delay)
        sleep_delay *= multiplier
        if sleep_delay > max_threshold:
            sleep_delay = max_threshold
