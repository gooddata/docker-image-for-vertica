#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (C) 2021 GoodData Corporation

import vertica_python
from typing import Tuple

import tests.config as config
import tests.cmd_utils as cmd_utils


class TestVerticaInstance:
    def test_db_up(self, db_system: Tuple[vertica_python.Connection, config.DbData]):
        conn, _ = db_system
        cur = conn.cursor('dict')
        cur.execute("select 1 as one")
        row = cur.fetchone()
        assert row['one'] == 1

    def test_vertica_version(self, db_system: Tuple[vertica_python.Connection, config.DbData]):
        conn, db_data = db_system
        cur = conn.cursor('dict')
        cur.execute("select version() as version")
        row = cur.fetchone()
        assert row['version'] == f"Vertica Analytic Database v{db_data.vertica_version}"

    def test_timezone(self, db_system: Tuple[vertica_python.Connection, config.DbData]):
        conn, db_data = db_system
        cur = conn.cursor('dict')
        cur.execute("show timezone")
        row = cur.fetchone()
        assert row['setting'] == db_data.vertica_setup.time_zone

    def test_os_user(self, db: config.DbData):
        os_user = cmd_utils.exec_cmd(f"docker exec -i {db.vertica_setup.vertica_container_name} whoami").rstrip()
        assert os_user == db.vertica_setup.db_user


class TestVerticaApp:
    def test_app_user(self, db_app: Tuple[vertica_python.Connection, config.DbData]):
        conn, _ = db_app
        cur = conn.cursor('dict')
        cur.execute("select 1 as one")
        row = cur.fetchone()
        assert row['one'] == 1

    def test_vmart_load(self, db_app: Tuple[vertica_python.Connection, config.DbData]):
        conn, db_data = db_app
        cur = conn.cursor('dict')
        cur.execute(f"select count(*) as sales_count from store.store_sales_fact")
        row = cur.fetchone()
        assert row['sales_count'] == db_data.vertica_setup.store_sales_fact_count
