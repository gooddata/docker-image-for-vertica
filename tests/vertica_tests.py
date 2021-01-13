#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (C) 2021 GoodData Corporation

import vertica_python
from tests.vertica_utils import poll_for_db
from tests.cmd_utils import exec_cmd


def get_conn_info(host, vertica_setup):
    return {
        'host': host,
        'port': vertica_setup['exposed_port'],
        'user': vertica_setup['db_user'],
        'password': vertica_setup['db_password'],
        'database': vertica_setup['db_name'],
        'connection_timeout': 60
    }


def get_conn_info_app(host, vertica_setup):
    conn_info = get_conn_info(host, vertica_setup)
    conn_info['user'] = vertica_setup['app_db_user']
    conn_info['password'] = vertica_setup['app_db_password']
    return conn_info


def test_db_up(host, vertica_setup, vertica_container_name):
    print("Test is DB UP ...")
    conn_info = get_conn_info(host, vertica_setup)
    assert poll_for_db(conn_info, vertica_setup, vertica_container_name)


def test_vertica_version(host, vertica_setup, vertica_version):
    print("Test Vertica version ...")
    conn_info = get_conn_info(host, vertica_setup)
    expected_version = f"Vertica Analytic Database v{vertica_version}"
    with vertica_python.connect(**conn_info) as conn:
        cur = conn.cursor('dict')
        cur.execute("select version() as version")
        result = cur.fetchall()
        # assert result[0]['version'] == vertica_version
        if result[0]['version'] == expected_version:
            print("Test passed")
        else:
            print(f"Test failed expected={expected_version} got={result[0]['version']}")


def test_app_user(host, vertica_setup):
    print(f"Test APP DB user named {vertica_setup['app_db_user']} ...")
    conn_info = get_conn_info_app(host, vertica_setup)
    try:
        with vertica_python.connect(**conn_info) as conn:
            cur = conn.cursor('dict')
            cur.execute("select 1")
            print("Test passed")
    except Exception as e:
        print(f"Test failed: {str(e)}")


def test_os_user(vertica_container_name, vertica_setup):
    print(f"Test OS user named {vertica_setup['db_user']} ...")
    os_user = exec_cmd(f"docker exec -it {vertica_container_name} whoami").rstrip()
    if os_user == vertica_setup['db_user']:
        print('Test passed')
    else:
        print(f"Test failed expected={vertica_setup['db_user']} got={os_user}")


def test_vmart_load(host, vertica_setup):
    print(f"Test VART load ...")
    conn_info = get_conn_info_app(host, vertica_setup)
    with vertica_python.connect(**conn_info) as conn:
        cur = conn.cursor('dict')
        cur.execute(f"select count(*) as sales_count from store.store_sales_fact")
        result = cur.fetchall()
        if result[0]['sales_count'] == vertica_setup['store_sales_fact_count']:
            print("Test passed")
        else:
            print(f"""
            Test failed 
            expected_store_sales_fact={vertica_setup['store_sales_fact_count']} got={result[0]['sales_count']}
            """)


def test_timezone(host, vertica_setup):
    print(f"Test timezone ...")
    conn_info = get_conn_info_app(host, vertica_setup)
    with vertica_python.connect(**conn_info) as conn:
        cur = conn.cursor('dict')
        cur.execute(f"show timezone")
        result = cur.fetchall()
        if result[0]['setting'] == vertica_setup['time_zone']:
            print("Test passed")
        else:
            print(f"Test failed expected_time_zone={vertica_setup['time_zone']} got={result[0]['setting']}")


def test_remove_packages(host, vertica_setup):
    print(f"Test remove_packages {vertica_setup['remove_packages']} ...")
    conn_info = get_conn_info_app(host, vertica_setup)
    with vertica_python.connect(**conn_info) as conn:
        for remove_package in vertica_setup['remove_packages'].split(' '):
            cur = conn.cursor('dict')
            cur.execute(f"select count(*) as lib_count from user_libraries where lib_name ilike '{remove_package}'")
            result = cur.fetchall()
            if result[0]['lib_count'] == 0:
                print("Test passed")
            else:
                print(f"Test failed - package {remove_package} was installed despite it is part of remove_packages")
