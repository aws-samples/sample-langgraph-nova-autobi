"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0
"""

from langchain.tools import BaseTool, StructuredTool, tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_aws import ChatBedrockConverse
from ..config import SQL_GENERATION_MODEL_ID
from ..prompts.prompt_text_sql import system_prompt_text_SQL
from datetime import date

def get_response(response, tag):
    response = BeautifulSoup(response).find_all(tag)[0].string.rstrip()
    return response

def create_agent_SQL(llm):
    """Create an agent."""
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system", system_prompt_text_SQL,
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    prompt = prompt.partial(date=date.today())
    return prompt | llm

bedrock_llm_SQL = ChatBedrockConverse(
                    model=SQL_GENERATION_MODEL_ID,
                    max_tokens = 1024,
                    temperature = 0.0
                )

create_SQL_agent = create_agent_SQL(
    llm = bedrock_llm_SQL
)

@tool
def sql_creation_tool(question):
    """
    Create sql code based on the user question

    Args:
        question (str): user question

    Returns:
        result (dict): result
    """
    result = create_SQL_agent.invoke({"messages":[question]})    
    return result.content