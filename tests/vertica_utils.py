#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (C) 2021 GoodData Corporation

import time
import vertica_python
from tests.cmd_utils import exec_cmd


def poll_for_db(conn_info, vertica_setup, vertica_container_name):
    start = time.time()
    while (time.time() - start) < vertica_setup['db_start_timeout']:
        try:
            output = exec_cmd(f"docker logs --tail 1 {vertica_container_name}").rstrip()
            if output == 'Vertica is now running':
                with vertica_python.connect(**conn_info) as conn:
                    cur = conn.cursor('dict')
                    cur.execute("select 1")
            else:
                time.sleep(10)
                print(f"DB is not yet ready, last msg from container: {output}")
                continue
        except vertica_python.errors.ConnectionError:
            duration = int((time.time() - start)*1000)
            time.sleep(10)
            print(f"DB is not yet ready, duration={duration}, waiting ...")
        else:
            return True
    return False
