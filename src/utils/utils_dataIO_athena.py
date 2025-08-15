"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0
"""

import json
import pandas as pd
import boto3
from time import sleep
from io import StringIO

class ATHENA_IO:
    def __init__(self, args):
        self.args = args
        self.client = boto3.client('athena', region_name=args.region_name)
        self.s3_output = args.s3_output
        self.database = args.database
        self.workgroup = args.workgroup

    def run_query(self, query):
        time_var = 5
        response = self.client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={'Database': self.database},
            ResultConfiguration={'OutputLocation': self.s3_output},
            WorkGroup=self.workgroup
        )
        query_execution_id = response['QueryExecutionId']
        
        status = 'RUNNING'
        while status in ['RUNNING', 'QUEUED']:
            response = self.client.get_query_execution(QueryExecutionId=query_execution_id)
            print(response)
            status = response['QueryExecution']['Status']['State']
            if status in ['FAILED', 'CANCELLED']:
                raise Exception(f'Athena query failed with Exception {response["QueryExecution"]["Status"]["StateChangeReason"]}')
            sleep(time_var)

        return query_execution_id

    def fetch_results(self, query_execution_id):
        response = self.client.get_query_results(QueryExecutionId=query_execution_id)
        print(response)
        result_data = response['ResultSet']['Rows']
        columns = [col['VarCharValue'] for col in result_data[0]['Data']]
        data = [[col.get('VarCharValue', None) for col in row['Data']] for row in result_data[1:]]
        df = pd.DataFrame(data, columns=columns)
        return df

    def read_athena(self, query):
        query_execution_id = self.run_query(query)
        return self.fetch_results(query_execution_id)

    def write_to_s3(self, df, s3_path):
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        s3_resource = boto3.resource('s3')
        bucket, key = s3_path.replace("s3://", "").split("/", 1)
        s3_resource.Object(bucket, key).put(Body=csv_buffer.getvalue())

    def execute_command(self, command):
        self.run_query(command)
        print("Executed successfully: ", command)
