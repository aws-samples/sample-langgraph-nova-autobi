"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0
"""

import pandas as pd
import os 
import warnings
from datetime import date
import json
from bs4 import BeautifulSoup
from datetime import datetime
import functools
from typing import Annotated, Literal
from typing_extensions import TypedDict

from IPython.display import Image, display

import boto3
from botocore.config import Config

from langchain.globals import set_debug
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool
from langchain_aws import ChatBedrock, ChatBedrockConverse
from langchain_core.messages import BaseMessage, ToolMessage
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate,MessagesPlaceholder
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    ToolMessage,
    RemoveMessage,
    AIMessage
)

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.prebuilt import create_react_agent
from langgraph.graph import END, StateGraph, START
import streamlit as st

# from util.agent_helper import load_tools

set_debug(False)
warnings.filterwarnings("ignore")

from src.tools.create_python import python_creation_tool
from src.tools.create_sql import sql_creation_tool
from src.tools.execute_python import python_execution_tool
from src.tools.execute_sql import sql_execution_tool

# from src.prompts.prompt_text_sql import system_prompt_text_SQL

st.set_page_config(
        page_title="User Dashboard",
        page_icon="👤",
        layout="wide",
        initial_sidebar_state="expanded"
    )

# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# from langgraph.graph import END, StateGraph, START

# from langchain_core.messages import AIMessage

#from util.agent_helper import load_tools

set_debug(False)
warnings.filterwarnings("ignore")
# First, let's set up our Streamlit app
#st.title("Customer Service Assistant")


USERNAME = ['User 1']
# def load_tools(
#         tool_names: list[str],
#         fail_on_missing: bool = True,
#         **kwargs: Any,
# ) -> list[Tool]:
#     """ Builds the tools for an agent given a list of tool names """
    
#     if not tool_names:
#         logger.warning("Agent query has no tools specified - using the dummy tool")
#         return [dummy_tool]
    
#     tools = []
#     missing = []
#     for name in tool_names:
#         parts = name.split(':', 1)
#         if len(parts) != 2:
#             print(f"error: Invalid tool name: {name}")
#             raise ValueError(f"Invalid tool name. Must be in the form module:tool. Found: '{name}'")
#         tool_module, tool_name = parts
        
#         loaded_tools = load_tools_from_package(
#             tool_kwargs=kwargs,
#             module_pattern=tool_module,
#             tool_pattern=tool_name,
#         )
#         if not loaded_tools:
#             missing.append(name)
#         else:
#             tools.extend(loaded_tools)
        
#     if missing:
#         missing_str = ", ".join(missing)
#         print(".error: Ignoring tools names we could not find: %s", missing_str)
#         if fail_on_missing:
#             raise ValueError(f"Could not find tools: {missing_str}")
            
#     return tools


class State(TypedDict):
    messages: Annotated[list, add_messages]

from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool

tools = [
    sql_creation_tool,
    sql_execution_tool,
    python_creation_tool,
    python_execution_tool,
]
tool_node = ToolNode(tools=tools)

system_prompt_text = """
You are a helpful assistant. Help the user answer any questions.
You have access to Insurance and eclaims data through a number of tools and chat_history.
<instructions>
Only answer what is asked.
Do not plot if not asked by the user.
If you have a figure that needs to be shown to the user. Use html <img> tags to show the figure.
</instructions>


<tools>
{tool_names}
</tools>

Always excute the sql.
Return the dataframe in pretty markdown format.

For referance today's date is {date}.
"""



# prompt = PromptTemplate(
#         template=system_prompt_text_rewriter,
#         input_variables=["question", "context"],
#     )

# rewriter_chain = prompt | bedrock_llm_rewriter

def get_response(response, tag):
    response = BeautifulSoup(response).find_all(tag)[0].string.rstrip()
    return response

def extract_and_format_messages(messages):
    formatted_output = ""
    
    for i in range(0, len(messages), 3):
        if i+2 < len(messages):
            human_message = messages[i]
            rewriter_message = messages[i+1]
            ai_message = messages[i+2]
            
            if isinstance(human_message, HumanMessage) and isinstance(rewriter_message, HumanMessage) and isinstance(ai_message, AIMessage):
                formatted_output += f"<Question> : {human_message.content.strip()}\n"
                formatted_output += f"<Rewritten Question>: {rewriter_message.content.strip()}\n"
                formatted_output += f"<Response> : {ai_message.content.strip()}\n\n"
    
    return formatted_output.strip()


# Helper function to create a node for a given agent
def plan_agent_node(state, agent, name):
    print(state)
    result = agent.invoke(state)
    # We convert the agent output into a format that is suitable to append to the global state
    if isinstance(result, ToolMessage):
        pass
    else:
        result = AIMessage(**result.dict(exclude={"type", "name"}), name=name)

    return {
        "messages": [result],
        # Since we have a strict workflow, we can
        # track the sender so we know who to pass to next.
        "sender": name,
    }

def create_agent(llm, tools, system_message: str):
    """Create an agent."""
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",system_prompt_text,
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    prompt = prompt.partial(date=date.today())
    prompt = prompt.partial(system_message=system_message)
    prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
    return prompt | llm.bind_tools(tools)



def route_tools(
    state: State,
) -> Literal["tools", "__end__"]:
    """
    Use in the conditional_edge to route to the ToolNode if the last message
    has tool calls. Otherwise, route to the end.
    """
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        # print(ai_message)
        return "tools"
    return "__end__"

def initialize_graph():
    # Initialize client
    bedrock_model_id = st.session_state['modelId']#"us.anthropic.claude-3-5-sonnet-20241022-v2:0"# 


    bedrock_llm = ChatBedrockConverse(
        model = bedrock_model_id,
        max_tokens = 1024,
        temperature = 0.0
    )

    create_plan_agent = create_agent(
        llm = bedrock_llm,
        tools = tools,
        system_message="",
    )
    plan_agent = functools.partial(plan_agent_node, agent=create_plan_agent, name="plan_agent")

    graph_builder = StateGraph(State)
    graph_builder.add_node("plan_agent", plan_agent)
    graph_builder.add_node("tools", tool_node)

    graph_builder.add_edge(START, "plan_agent")
    graph_builder.add_conditional_edges(
        "plan_agent",
        route_tools,
        {"tools": "tools", "__end__": "__end__"},
    )

    graph_builder.add_edge("tools", "plan_agent")

    memory = MemorySaver()
    graph = graph_builder.compile(checkpointer=memory)
    return graph




def initialize_session_state():
    """Initialize session state variables"""
    if 'selected_user' not in st.session_state:
        st.session_state.selected_user = None
    if 'last_update' not in st.session_state:
        st.session_state.last_update = None
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "model" not in st.session_state:
        st.session_state['modelId'] = None
    if "conversation_history" not in st.session_state:
        st.session_state['conversation_history'] = {u:[] for u in USERNAME}
    if 'context' not in st.session_state:
        st.session_state.context = ""
        
# def clear_cache():
#     checkpoint = empty_checkpoint()
#     memory.put(config={"configurable": {"thread_id": thread_id}}, checkpoint=checkpoint, metadata={})

def sidebar_user_selection():
    """Create sidebar with user selection"""
    bedrock_models = {
        "Amazon Nova Pro": "us.amazon.nova-pro-v1:0",
        "Amazon Nova Lite": "us.amazon.nova-lite-v1:0", 
        "Amazon Nova Micro": "us.amazon.nova-micro-v1:0",
        "Sonnet": "anthropic.claude-3-sonnet-20240229-v1:0", 
        "Sonnet35": "us.anthropic.claude-3-5-sonnet-20240620-v1:0",
    }
    with st.sidebar:
        st.title("Admin Tools")
        ai_model = st.selectbox(
            label="Language model:",
            options=list(bedrock_models.keys()),
            key="ai_model",
            help="The search app provides flexibility to choose a large language model used for AI answers.",)
        st.session_state['modelId'] = bedrock_models[ai_model]
        print("Bedrock Models", bedrock_models[ai_model])
        # User selector
        selected_user = st.selectbox(
            "Choose a user:",
            options=USERNAME,
            #format_func=lambda x: data['users'][x]['name']['first_name']+' '+data['users'][x]['name']['last_name']
        )
        
        if selected_user != st.session_state.selected_user:
            st.session_state.selected_user = selected_user
            st.session_state.last_update = datetime.now()
        
        # Display user info
        # if selected_user:
        #     st.divider()
        #     st.subheader("User Information")
        #     user_config = data['users'][selected_user]
        #     st.write(f"Name: {user_config['name']['first_name']} {user_config['name']['last_name']}")
        #     st.write(f"Email: {user_config['email']}")
        #     st.write(f"Address: {user_config['address']['address1']} {user_config['address']['address2']} {user_config['address']['city']} {user_config['address']['province']} {user_config['address']['country']} {user_config['address']['zip']}")
        #     st.write(f"Payment Methods:", list(user_config['payment_methods'].keys()))
        #     st.write(f"Orders:", user_config['orders'])
            
        #st.button("clear cache", type="primary",on_click=clear_cache)


def main_content(graph = None):
    """Display main content"""
    if st.session_state.selected_user:
        #user_config = data['users'][st.session_state.selected_user]
        
        # Main header
        st.title(f"Welcome!")

        # user_input = st.text_input("How can I help you today?")
        #config['user_info'] = user_config
        #thread['configurable']['thread_id'] = st.session_state.selected_user            

        # Chat input
        if user_input := st.chat_input("Type your message here..."):
            # Create initial state
            st.session_state.messages.append(HumanMessage(content=user_input))
            st.session_state.conversation_history[st.session_state.selected_user].append(HumanMessage(content=user_input))
            # Process through the graph
            with st.spinner('Processing...'):
                human_question = f"""
                    Question: {user_input}
                    """
                response = graph.stream({
                    "messages": [('human',human_question)]
                    #"current_step": "start"
                }, config = st.session_state['config'])
                for event in response:
                    print("Event", event)
                final_state = event
                st.session_state.conversation_history[st.session_state.selected_user].append(final_state['plan_agent']['messages'][0])
            print(final_state, st.session_state.messages)
#         # Control buttons
        # Chat interface
        chat_container = st.container()

        with chat_container:
            # Display conversation history
            for message in st.session_state.conversation_history[st.session_state.selected_user]:
                print("Message", message, type(message))
                with st.chat_message('human' if isinstance(message, HumanMessage) else 'ai'):
                    st.markdown(message.content)
    else:
        st.warning("Please enter your in the sidebar to continue.")


def main():
    """Main application"""

    # Initialize session state
    initialize_session_state()
    
    # Create sidebar
    sidebar_user_selection()
    if 'graph' not in st.session_state:
        st.session_state['graph'] = initialize_graph()
        st.session_state['messages'] = []
        st.session_state['config'] = {
            "configurable": {
                "thread_id": st.session_state.selected_user
            },
            "recursion_limit": 20
        }

    # Display main content
    main_content(st.session_state['graph'])

if __name__ == "__main__":
    main()
