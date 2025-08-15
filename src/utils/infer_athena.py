"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0
"""

import re
import boto3
import base64
import logging
import pandas as pd
from datetime import date
from ..config import AWS_REGION

from .invoke_bedrock import generate_bedrock_claude_response
from .athena_connector import execute_sql

logger = logging.getLogger(__name__)

runtime = boto3.client("bedrock-runtime",AWS_REGION)


# Extract XML content
def extract_xml_content(string,tag=''):
    
    pattern = re.compile(f'<{tag}>[^\r]*?</{tag}>')
    xml_raw = pattern.findall(string.replace("\r",""))
    xml_content = [xml.replace(f'<{tag}>','').replace(f'</{tag}>','') for xml in xml_raw]
    
    return xml_content

# Post-process SQL query
def sql_post_process(sql):
    # Removed sensitive data; dummy function for now
    return sql

# Question rewriter
def rewrite_question(user_question,
                     context,
                     llm_rewriter,
                     prompt_template_rewriter,
                     bedrock_runtime):
    
    prompt_rewriter = prompt_template_rewriter.replace("{question}", user_question)
    prompt_rewriter = prompt_rewriter.replace("{context}", context)
    # print("PROMPT REWRITER", prompt_rewriter)
    
    generated_response_ques = generate_bedrock_claude_response(bedrock_runtime, 
                                           prompt_rewriter,
                                           model_name=llm_rewriter)
    
    print(generated_response_ques)
    rewritten_ques = extract_xml_content(generated_response_ques, "response")[0]
    
    # print("REWRITTEN QUESTION", rewritten_ques)
    return rewritten_ques

# Router
def route_question(question,
                   llm_router,
                   prompt_template_router,
                   bedrock_runtime):
    
    prompt_router = prompt_template_router.replace("{question}", question)
    
    generated_response_workflow = generate_bedrock_claude_response(bedrock_runtime, 
                                           prompt_router,
                                           model_name=llm_router)
    
    workflow = extract_xml_content(generated_response_workflow, "response")[0] # 'SQL' or 'Python'
    print("WORKFLOW", workflow)
    
    return workflow


# Text2SQL
def generate_text2sql(user_question, llm_text2sql, prompt_template_text2sql, bedrock_runtime):
    prompt_text2sql = prompt_template_text2sql.replace("{question}", user_question)
    prompt_text2sql = prompt_text2sql.replace("{schema}", "")
    prompt_text2sql = prompt_text2sql.replace("{categories}", "")
    prompt_text2sql = prompt_text2sql.replace("{date}", date.today().strftime("%Y-%m-%d"))
    
    generated_response_sql = generate_bedrock_claude_response(bedrock_runtime, 
                                           prompt_text2sql,
                                           model_name=llm_text2sql) 
    print("GENERATED RESPONSE SQL", generated_response_sql)
    print("END GENERATED RESPONSE")
    
    if llm_text2sql in ["Claude3Sonnet", "Claude3Haiku"]:
        generated_response_sql = generated_response_sql + "</reasoning>"
    else:
        generated_response_sql = "<SQL> SELECT " + generated_response_sql + "</reasoning>"
        
    try:
        sql_query = extract_xml_content(generated_response_sql, "SQL")[0]
        sql_reasoning = extract_xml_content(generated_response_sql, "reasoning")[0]

        ########### append shortlisting message ###############
        shortlisting_message = "Based on the question, the most suitable database is ‘insurance_and_eClaims’.\nThe shortlisted tables within this database are  ['Customers', 'Staff', 'Policies', 'Claim_Headers', 'Claims_Documents', 'Claims_Processing_Stages', 'Claims_Processing'].\n"
        sql_reasoning = shortlisting_message + sql_reasoning
        ########### append shortlisting message ###############

    except IndexError:
        print("Failed to extract SQL query from response")
        sql_query = ""
        sql_reasoning = ""
    return sql_query, sql_reasoning

# Data2Text
def generate_data2text(user_question, sql_query, llm_data2text, athena_args, prompt_template_data2text, bedrock_runtime):
    try:
        # Execute SQL query using the existing execute_sql function
        
        queried_data_df = execute_sql(
            sql = sql_query,
            args = athena_args
        )
        
        # Convert DataFrame to string
        queried_data_str = queried_data_df.to_string()
        
        # Prepare prompt
        prompt_data2text = prompt_template_data2text.replace("{question}", user_question)
        prompt_data2text = prompt_data2text.replace("{data_retrieved}", queried_data_str)
        
        # Generate response
        generated_response_text = generate_bedrock_claude_response(bedrock_runtime, 
                                               prompt_data2text,
                                               model_name=llm_data2text)
        
        generated_response_text = extract_xml_content(generated_response_text, "response")[0]
        
        # Log the DataFrame columns
        logger.info(f"DataFrame columns: {queried_data_df.columns}")
        
        return queried_data_df, generated_response_text
    except Exception as e:
        logger.error(f"Error in generate_data2text: {e}")
        return None, None

# Text2Python
def generate_text2python(user_question, llm_text2python, prompt_template_text2python, bedrock_runtime, df_info=None):
    prompt_template_text2python = prompt_template_text2python.replace("{date}", date.today().strftime("%Y-%m-%d"))
    if df_info is not None:
        prompt_text2python = prompt_template_text2python.replace("{question}", user_question)
        prompt_text2python = prompt_text2python.replace("{columns}", ', '.join(df_info))
    else:
        prompt_text2python = prompt_template_text2python.replace("{question}", user_question)
    
    generated_response_python = generate_bedrock_claude_response(bedrock_runtime, 
                                           prompt_text2python,
                                           model_name=llm_text2python,
                                           max_tokens=1024)
    
    python_code = extract_xml_content(generated_response_python, "response")[0]
    python_reasoning = extract_xml_content(generated_response_python, "reasoning")[0]
    
    return python_code, python_reasoning

def execute_python(python_code, queried_data_df, conversation_context):
    try:
        if queried_data_df.empty:
            raise ValueError("The queried DataFrame is empty.")
        
        print("DataFrame is not empty.")
        print("DataFrame head:")
        print(queried_data_df.head())
        
        print("Executing Python code...")
        
        # Capture the Python execution output
        import io
        import sys
        stdout_backup, stderr_backup = sys.stdout, sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        
        try:
            # Set up the execution environment
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import pandas as pd
            import numpy as np
            import os

            # Prepare the execution environment
            exec_globals = {
                'df': queried_data_df,
                'plt': plt,
                'pd': pd,
                'np': np,
                'sys': sys
            }

            # Execute the Python code as generated
            exec(python_code, exec_globals)

        except Exception as e:
            print(f"Error executing Python code: {str(e)}")
        
        stdout_output = sys.stdout.getvalue()
        stderr_output = sys.stderr.getvalue()
        print("SDT OUTPUT", stdout_output)
        print("SDT error", stderr_output)
        sys.stdout, sys.stderr = stdout_backup, stderr_backup
        print(stderr_output)
        
        # Check if the figure was created and saved
        fig = None
        if os.path.exists('figure.png'):
            fig = 'figure.png'
            print("Figure created successfully.")
        else:
            print("No figure was created.")

        with open("figure.png", "rb") as image_file:
            image_bytes = image_file.read()

        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        
        return fig, encoded_image
        
    except FileNotFoundError as e:
        print(f"Error: {str(e)}")
        fig = plt.figure()  # Create a blank figure
        return fig