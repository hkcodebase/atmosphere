from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver



from state import AgentState
from graph_nodes import agent_node, tools_node, should_call_tools


def build_graph():

    workflow = StateGraph(AgentState)

    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tools_node)

    workflow.set_entry_point("agent")

    workflow.add_conditional_edges(
        "agent",
        should_call_tools,
        {
            "tools": "tools",
            "end": END,
        },
    )

    workflow.add_edge("tools", "agent")

    # -------------------------
    # MEMORY (SQLite)
    # -------------------------

    memory = MemorySaver()

    return workflow.compile(checkpointer=memory)