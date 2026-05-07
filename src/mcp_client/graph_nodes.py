from langchain_core.messages import HumanMessage
from langgraph.prebuilt import ToolNode
from tools_lc import (
    get_location,
    get_forecast_by_location,
    get_alerts,
)
from llm import get_llm


llm = get_llm()

tools = [get_location, get_forecast_by_location, get_alerts]

tool_node = ToolNode(tools)

llm_with_tools = llm.bind_tools(tools)


# ---------------------------
# Agent Node (Reasoning)
# ---------------------------

def agent_node(state):
    messages = state["messages"]

    response = llm_with_tools.invoke(messages)

    return {
        "messages": messages + [response],
        "answer": response.content,
    }


# ---------------------------
# Tool Router Node
# ---------------------------

def should_call_tools(state):
    last = state["messages"][-1]

    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return "end"


# ---------------------------
# Tool Execution Node
# ---------------------------

def tools_node(state):
    messages = state["messages"]

    tool_response = tool_node.invoke({"messages": messages})

    return {
        "messages": messages + tool_response["messages"],
    }