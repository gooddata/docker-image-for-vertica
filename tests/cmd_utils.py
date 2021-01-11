#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (C) 2021 GoodData Corporation

import subprocess


class SubProcessError(Exception):
    """
    Exception caused by unexpected return code from subprocess.
    """

    def __init__(self, cmd, return_code, stderr):
        super(SubProcessError, self).__init__()
        self.cmd = cmd
        self.return_code = return_code
        self.stderr = stderr

    def __str__(self):
        return 'cmd={0} return_code={1} stderr={2}'.format(self.cmd, self.return_code, self.stderr)


def exec_cmd(cmd, return_codes=(0,)):
    """
    Helper function to execute commands

    :param cmd: command to execute
    :param return_codes: list of valid return codes, default is [0]
    :return: stdout produced by the command
    """
    proc = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8', shell=True)
    (std_out, std_err) = proc.communicate()

    if proc.returncode not in return_codes:
        raise SubProcessError(cmd, proc.returncode, std_err)
    else:
        return std_out + std_err
