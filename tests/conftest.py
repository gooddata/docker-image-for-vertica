#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (C) 2021 GoodData Corporation

import pytest
import os
import tests.config as test_config
import tests.docker_utils as docker_utils
import vertica_python


cfg: test_config.Config = test_config.Config.from_file(
    os.environ.get('VERTICA_IMAGE_TEST_CONFIG', 'tests/config.yaml')
)


def pytest_addoption(parser):
    parser.addoption('--test-vmart', action='store_true', default=False,
                     help='Execute tests for VMART dataset')


@pytest.fixture(scope='session', **cfg.fixture_test_setup())
def db(request):
    load_data = request.config.getoption('test_vmart')
    db_data: test_config.DbData = request.param

    docker_utils.build_vertica_image(db_data.os_family, db_data.vertica_setup, db_data.os_version,
                                     db_data.vertica_version, db_data.vertica_tag)
    test_volume = docker_utils.create_docker_volume(db_data.vertica_tag)
    try:
        try:
            docker_utils.run_vertica_container(db_data.vertica_setup, db_data.vertica_tag, test_volume, load_data)
            docker_utils.poll_for_db_service(db_data.vertica_setup)
            yield db_data
        finally:
            docker_utils.stop_docker_container(db_data.vertica_setup)
    finally:
        docker_utils.remove_docker_volume(test_volume)


@pytest.fixture(scope='session')
def db_system(db: test_config.DbData):
    with vertica_python.connect(**db.vertica_setup.get_system_connection_dict()) as conn:
        yield conn, db


@pytest.fixture(scope='session')
def db_app(db: test_config.DbData, request):
    load_data = request.config.getoption('test_vmart')
    if not load_data:
        pytest.skip('VMART dataset tests disabled')

    with vertica_python.connect(**db.vertica_setup.get_app_connection_dict()) as conn:
        yield conn, db
