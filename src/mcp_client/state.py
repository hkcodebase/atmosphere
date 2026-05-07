from typing import TypedDict, List, Optional


class AgentState(TypedDict):
    messages: List
    question: str
    answer: str