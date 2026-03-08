import os
import time

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field
import logging
from typing_extensions import TypedDict
from langchain_core.messages import HumanMessage, SystemMessage

from pytick.llm.agents.converter import converter_agent
from pytick.llm.agents.router import router
from pytick.llm.agents.validator import validator_agent
from pytick.llm.llm_types import State
from pytick.llm.utility import draw_graph
from pytick.utility.utility import clean_gherkin, get_logger, read_config, read_file

logger = get_logger(__file__, logging.DEBUG)


class Graph:
    """Handler for LLM-based Gherkin conversion and validation."""

    def __init__(self, system_prompt: str, retry_prompt: str, ollama_model: str = "", openai_model: str = ""):
        # Global state to maintain conversation across calls
        self.conversation_state = State(
            messages=[], message_type=None, errors=[])
        self.system_prompt = system_prompt
        self.retry_prompt = retry_prompt
        if ollama_model == "" and openai_model == "":
            raise Exception(
                "Please define a model for either Ollama or OpenAI")
        if ollama_model != "":
            self.llm = ChatOllama(model=ollama_model, temperature=0)
        if openai_model != "":
            self.llm = init_chat_model(f"{openai_model}", temperature=0.1)
        self.__build_graph()

    def __build_graph(self):
        graph_builder = StateGraph(State)
        graph_builder.add_node("validator", self.bound_validator_agent)
        graph_builder.add_node("router", router)
        graph_builder.add_node("converter", self.bound_converter_agent)

        graph_builder.add_edge(START, "converter")
        graph_builder.add_edge("converter", "validator")
        graph_builder.add_edge("validator", "router")
        # graph_builder.add_edge("validator", END)
        graph_builder.add_conditional_edges(
            source="router",
            path=lambda state: state.get("message_type"),
            path_map={"valid": END, "invalid": "converter",
                      "max_retries": END},
        )

        self.graph = graph_builder.compile()

    def run(self, user_input: str) -> str:
        """Run the chatbot with a sample message."""
        # Add the new user message to the existing conversation
        user_message = HumanMessage(content=user_input)
        llm_state = State(
            messages=[user_message],
            message_type=None,
            errors=[],
            retry_count=0,
            system_prompt=self.system_prompt,
            retry_prompt=self.retry_prompt
        )

        # Invoke the graph with the current conversation state
        result_state = self.graph.invoke(llm_state)
        if result_state.get("message_type", "") == "max_retries":
            logger.warning("Max retries reached. Ending conversation.")
            return "Max retries reached. Please try again later."
        last_message = result_state["messages"][0]
        return clean_gherkin(last_message.content)

    # Create bound agent functions that include the LLM
    def bound_validator_agent(self, state: State) -> State:
        return validator_agent(state, self.llm)

    def bound_converter_agent(self, state: State) -> State:
        return converter_agent(state=state, llm=self.llm)


if __name__ == "__main__":
    load_dotenv()
    config = os.environ.get("CONFIG_FILE")
    app_config = read_config(file_path=config)
    prompt = read_file(file_path=os.path.join(app_config.get(
        'app_data_path', ''), "llm_prompt_init.prompt.md"))
    retry_prompt = read_file(file_path=os.path.join(app_config.get(
        'app_data_path', ''), "llm_prompt_retry.prompt.md"))

    test_messages = [
        # "sma20 < close",
        "ema10 > close and close > atr and close > 1000",
        # "close > vwap",
    ]
    handler = Graph(system_prompt=prompt,
                    retry_prompt=retry_prompt, ollama_model="phi4")
    for msg in test_messages:
        start = time.perf_counter()
        print(f"----Input: {msg}----")
        print(handler.run(msg))
        print(f"----time taken: {time.perf_counter() - start}----")

    # draw_graph(graph, "ai/gherkin/converter/state_graph.png")
