"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0
"""

from ..prompts.prompt_text_python import system_prompt_text_python
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import pandas as pd
from langchain_aws import ChatBedrockConverse
from ..config import PYTHON_GENERATION_MODEL_ID

model_kwargs = { 
    "max_tokens": 1024,
    "temperature": 0.0,
    "top_k": 250,
    "top_p": 1,
    "stop_sequences": ["Human"],
}

bedrock_llm_python = ChatBedrockConverse(
    model=PYTHON_GENERATION_MODEL_ID,
    max_tokens = 1024,
    temperature = 0.0
)

def create_agent_python(llm):
    """
    Create an agent.
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system", system_prompt_text_python,
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    return prompt | llm


create_python_agent = create_agent_python(
    llm=bedrock_llm_python
)


@tool
def python_creation_tool(df, question):
    """
    Create python code based on the question and data (df). Used for plotting.

    Args:
        df (dict): df in a json format
        question (str): user question

    Returns:
        result (dict): result
    """

    df = pd.DataFrame.from_dict(df)

    result = create_python_agent.invoke({"messages": [question], "df": df})
    return result.content