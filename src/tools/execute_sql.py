"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0
"""

from ..utils.athena_connector import execute_sql
from langchain.tools import tool
import os
from..config import AWS_REGION, DATABASE_NAME, ATHENA_S3_OUTPUT, ATHENA_WORKGROUP

athena_config = {
    'region_name': os.environ.get("AWS_REGION", AWS_REGION),
    'database': os.environ.get("ATHENA_DATABASE", DATABASE_NAME),
    's3_output': os.environ.get("ATHENA_S3_OUTPUT", ATHENA_S3_OUTPUT),
    'workgroup': os.environ.get("ATHENA_WORKGROUP", ATHENA_WORKGROUP)
}

@tool(return_direct=True)
def sql_execution_tool(sql):
    """
    Execute the sql code in Athena

    Args:
        sql: sql code to execute

    Returns:
        result (DataFrame): result in a df format
    """
    response = execute_sql(sql, athena_config)
    
    print("++++++++++++++++++++++++++")
    print(type(response))
    print(response)
    print("++++++++++++++++++++++++++")
    
    return response.to_html()