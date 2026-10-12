from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, SystemMessage

from models import get_model
from prompts import PROMPTS


class ChatState(TypedDict):
    provider: str
    prompt_key: str
    messages: list

builder = StateGraph(ChatState)

def call_model(state: ChatState) -> dict:
    model = get_model(state["provider"])
    system_msg = SystemMessage(content=PROMPTS.get(state["prompt_key"]))
    full_messages = [system_msg] + state["messages"]
    response = model.invoke(full_messages)
    return {"messages": [response]}


builder.add_node("call_model", call_model)
builder.add_edge(START, "call_model")
builder.add_edge("call_model", END)

graph = builder.compile()

def chat(provider: str, prompt_key: str, user_input: str) -> str:
    result = graph.invoke(
        {"provider": provider, "prompt_key": prompt_key, "messages": [HumanMessage(content=user_input)]}
    )

    # if provider == "gemma" or provider == "qwen":
    return result["messages"][-1].content
