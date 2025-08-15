"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0
"""

from langchain.tools import BaseTool, StructuredTool, tool
import pandas as pd
from ..utils.infer_athena import execute_python

@tool(response_format="content_and_artifact")
def python_execution_tool(code_python, df, question):
    """
    Execute the python code

    Args:
        code_python (str): Python code
        df (dict): df in a json format
        question (str): user question

    Returns:
        encoded image (str): encoded image
    """

    df = pd.DataFrame.from_dict(df)

    fig, response = execute_python(code_python, df, question)
    return "Figure created successfully", fig

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