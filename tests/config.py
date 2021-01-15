#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (C) 2021 GoodData Corporation

import yaml
import re
from typing import Dict, List, NamedTuple, Tuple, Optional
import vertica_python


class OsFamily:
    def __init__(self, config: Dict):
        self._config = config

    @property
    def name(self) -> str:
        return self._config['name']

    @property
    def os_versions(self) -> List[str]:
        return self._config['os_versions']


class VerticaSetup:
    def __init__(self, config: Dict, host_override: str = None):
        self._config = config
        self._host_override = host_override

    @property
    def host(self) -> str:
        if self._host_override:
            return self._host_override

        return self._config['host']

    @property
    def exposed_port(self) -> int:
        return self._config['exposed_port']

    @property
    def db_user(self) -> str:
        return self._config['db_user']

    @property
    def db_group(self) -> str:
        return self._config['db_group']

    @property
    def db_password(self) -> str:
        return self._config['db_password']

    @property
    def db_name(self) -> str:
        return self._config['db_name']

    @property
    def app_db_user(self) -> str:
        return self._config['app_db_user']

    @property
    def app_db_password(self) -> str:
        return self._config['app_db_password']

    @property
    def db_start_timeout(self) -> int:
        return self._config['db_start_timeout']

    @property
    def vmart_start_year(self) -> int:
        return self._config['vmart_start_year']

    @property
    def vmart_end_year(self) -> int:
        return self._config['vmart_end_year']

    @property
    def store_sales_fact_count(self) -> int:
        return self._config['store_sales_fact_count']

    @property
    def remove_packages(self) -> str:
        return self._config['remove_packages']

    @property
    def time_zone(self) -> str:
        return self._config['time_zone']

    @property
    def vertica_container_name(self) -> str:
        return self._config['vertica_container_name']

    def _get_connection_dict(self):
        return {
            'host': self.host,
            'port': self.exposed_port,
            'database': self.db_name,
            'connection_timeout': 60
        }

    def get_system_connection_dict(self):
        conn_dict = self._get_connection_dict()
        conn_dict['user'] = self.db_user
        conn_dict['password'] = self.db_password
        return conn_dict

    def get_app_connection_dict(self):
        conn_dict = self._get_connection_dict()
        conn_dict['user'] = self.app_db_user
        conn_dict['password'] = self.app_db_password
        return conn_dict


class DbData(NamedTuple):
    os_family: str
    os_version: str
    vertica_version: str
    vertica_tag: str
    vertica_setup: VerticaSetup


class TestData(DbData):
    conn: vertica_python.Connection


class Config:
    _instance = None

    def __init__(self, config_path: str, host_override: Optional[str] = None):
        self._config = self._load_config(config_path)
        self._host_override = host_override
        self._os_families = None
        self._vertica_setup = None

    @classmethod
    def from_file(cls, config_path: str, host_override: str = None):
        if not cls._instance:
            cls._instance = cls(config_path, host_override)

        return cls._instance

    @staticmethod
    def _load_config(config_path: str) -> Dict:
        with open(config_path, 'rt') as f:
            return yaml.safe_load(f)

    @property
    def vertica_repository(self):
        return self._config.get('vertica_repository', 'vertica')

    @property
    def os_families(self) -> List[OsFamily]:
        if not self._os_families:
            self._os_families = [OsFamily(family_config) for family_config in self._config['os_families']]
        return self._os_families

    @property
    def vertica_versions(self) -> List[str]:
        return self._config['vertica_versions']

    @property
    def vertica_setup(self) -> VerticaSetup:
        if not self._vertica_setup:
            self._vertica_setup = VerticaSetup(self._config['vertica_setup'], self._host_override)
        return self._vertica_setup

    def generate_test_setup(self) -> Tuple[List[DbData], List[str]]:
        tag_re = re.compile('[^a-z0-9_.-]', re.I)
        variants = []
        ids = []
        for os_family in self.os_families:
            for os_version in os_family.os_versions:
                for vertica_version in self.vertica_versions:
                    tmp_vertica_tag = f"{vertica_version}.{os_family.name}_{os_version}"
                    vertica_tag = f"{self.vertica_repository}:{tag_re.sub('_', tmp_vertica_tag)}"
                    variants.append(DbData(os_family.name, os_version, vertica_version,
                                           vertica_tag, self.vertica_setup))
                    ids.append(vertica_tag)

        return variants, ids

    def fixture_test_setup(self) -> Dict[str, List]:
        variants, ids = self.generate_test_setup()
        return {'params': variants, 'ids': ids}
