from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from langchain_core.messages import HumanMessage, SystemMessage

from pytick.llm.agents.converter import converter_agent
from pytick.llm.agents.router import router
from pytick.llm.agents.validator import validator_agent
from pytick.llm.types import State
from pytick.llm.utils.draw import draw_graph

load_dotenv()

llm = init_chat_model("openai:gpt-4o", temperature=0.1)


# Create bound agent functions that include the LLM
def bound_validator_agent(state: State) -> State:
    return validator_agent(state, llm)


def bound_converter_agent(state: State) -> State:
    return converter_agent(state, llm)


graph_builder = StateGraph(State)
graph_builder.add_node("validator", bound_validator_agent)
graph_builder.add_node("router", router)
graph_builder.add_node("converter", bound_converter_agent)

graph_builder.add_edge(START, "converter")
graph_builder.add_edge("converter", "validator")
graph_builder.add_edge("validator", "router")
# graph_builder.add_edge("validator", END)
graph_builder.add_conditional_edges(
    source="router",
    path=lambda state: state.get("next"),
    path_map={"valid": END, "invalid": "converter"},
)

graph = graph_builder.compile()

# Global state to maintain conversation across calls
conversation_state = {"messages": [], "message_type": None}


def plot_graph():
    """Plot the state graph."""
    draw_graph(graph, "ai/gherkin/converter/state_graph.png")


def debug_messages(messages):
    """Debug function to print messages in the conversation."""
    for i, msg in enumerate(messages):
        print(
            f"  {i}: {type(msg).__name__} - {msg.content if hasattr(msg, 'content') else ''}"
        )


def run_chatbot(user_input: str = "ema10>close and rsi > 80 and close > 1000") -> str:
    """Run the chatbot with a sample message."""
    global conversation_state

    # Add the new user message to the existing conversation
    user_message = HumanMessage(content=user_input)
    conversation_state["messages"] = conversation_state["messages"] + [user_message]

    # Invoke the graph with the current conversation state
    result_state = graph.invoke(conversation_state)

    # Update the global conversation state with the result
    conversation_state = result_state

    if conversation_state.get("messages") and len(conversation_state["messages"]) > 0:
        last_message = conversation_state["messages"][-1]
        # Retain only system messages to avoid state bloat
        conversation_state["messages"] = [m for m in conversation_state["messages"] if isinstance(m, SystemMessage)]
        return last_message.content
    return "Can't process request to gherkin"


if __name__ == "__main__":
    test_messages = [
        "sma20 < close",
        "add ema10 > close and rsi > 80 and close > 1000",
    ]

    for msg in test_messages:
        print(f"----Input: {msg}----")
        print(run_chatbot(msg))
    # draw_graph(graph, "ai/gherkin/converter/state_graph.png")
