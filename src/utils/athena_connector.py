"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0
"""

import argparse
from .utils_dataIO_athena import ATHENA_IO


class AthenaConnector:
    def __init__(self, args):
        self.args = args
        self.athena_io = ATHENA_IO(self.args)

    def execute_sql(self, sql):
        return self.athena_io.read_athena(sql)

def get_athena_conn(args):
    return AthenaConnector(args)

def execute_sql(sql, args):
    if isinstance(args, dict):
        # If args is already a dictionary, use it as is
        conn = get_athena_conn(argparse.Namespace(**args))
    elif isinstance(args, argparse.Namespace):
        # If args is a Namespace object, convert it to a dictionary
        conn = get_athena_conn(args)
    else:
        raise ValueError("args must be either a dictionary or an argparse.Namespace object")
    
    athena_io = conn.athena_io
    result_df = athena_io.read_athena(sql)
    print(result_df)
    return result_df