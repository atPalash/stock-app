
from pytick.utility.utility import clean_gherkin, get_logger, read_config, read_file
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel
from collections.abc import Callable
from pytick.llm.graph import Graph
from pytick.llm.common_agents.converter import converter_agent as common_converter
from pytick.llm.common_agents.validator import validator_agent as common_validator
from pytick.llm.common_agents.router import router as common_router
from pytick.llm.gherkin_agents.converter import converter_agent as gherkin_converter
from pytick.llm.gherkin_agents.validator import validator_agent as gherkin_validator
from pytick.llm.gherkin_agents.router import router as gherkin_router
from pytick.llm.classifier_agents.validator import validator_agent as classifier_validator
from pytick.llm.search_agents.converter import converter_agent as search_converter
import logging
from pytick.llm.llm_types import State
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pytick.llm.utility import draw_graph

logger = get_logger(__file__, logging.DEBUG)


class MultiGraph:
    """Handler for LLM-based Gherkin conversion and validation."""

    def __init__(self, classifier: Graph, default: Graph, **workers):
        self.workers = workers
        self.workers['default'] = default
        supported_capabilities = []
        worker_ids = []
        for id, worker in self.workers.items():
            supported_capabilities.append(
                f'{id}: {worker.system_prompt}')
            worker_ids.append(id)
        valid_workers = ', '.join(f'{wid}' for wid in worker_ids)
        capablities = f"""Supported capabilities:
{chr(10).join(supported_capabilities)}

VALID_WORKERS: {valid_workers}"""
        self.classifier = classifier
        self.classifier.update_system_prompt(prompt_to_add=capablities)
        self.__build_graph()

    def __build_graph(self):
        graph_builder = StateGraph(State)
        graph_builder.add_node("classifier", self.classifier.graph)
        graph_builder.add_node("route_decision", self.route_decision_node)

        # Dynamically add worker nodes
        for worker_id, worker in self.workers.items():
            graph_builder.add_node(worker_id, worker.graph)

        graph_builder.add_edge(START, "classifier")
        graph_builder.add_edge("classifier", "route_decision")
        graph_builder.add_conditional_edges(
            source="route_decision",
            path=lambda state: state.get("message_type"),
            path_map={**{wid: wid for wid in self.workers.keys()},
                      "max_retries": END},
        )

        # Add edges from workers to END
        for worker_id in self.workers.keys():
            graph_builder.add_edge(worker_id, END)

        self.graph = graph_builder.compile()

    def get_graph(self):
        return self.graph.get_graph(xray=True)

    def run(self, user_input: str) -> str:
        """Run the classifier with a sample message."""
        # Add the new user message to the existing conversation
        user_message = HumanMessage(content=user_input)
        llm_state = State(
            messages=[user_message],
            message_type="valid",
            errors=[],
            retry_count=0,
            system_prompt=self.classifier.system_prompt,
            retry_prompt=self.classifier.retry_prompt
        )

        # Invoke the graph with the current conversation state
        result_state = self.graph.invoke(llm_state)
        if result_state.get("message_type", "") == "max_retries":
            logger.warning("Max retries reached. Ending conversation.")
            return "Max retries reached. Please try to improve query."
        last_message = result_state["messages"][0]
        return last_message.content

    def route_decision_node(self, state: State) -> dict:
        worker_id = state.get("messages", [])[
            0].content if state.get("messages") else "chat"
        if state.get("message_type") == "max_retries":
            worker_id = "default"
        worker = self.workers[worker_id]
        # logger.debug(
        #     f"Routing to worker: {worker_id} based on input: '{state.get('messages', [])[-1].content}'")
        return {
            "message_type": worker_id,
            "retry_count": 0,
            "errors": [],
            "system_prompt": worker.system_prompt,
            "retry_prompt": worker.retry_prompt,
        }


if __name__ == "__main__":
    classifier_system_prompt = f"""Your are to choose one of the capability among

CRITICAL INSTRUCTIONS:
1. You MUST respond with ONLY one of these VALID_WORKERS
2. Your response must be a single word, nothing else
3. Do NOT include any explanation, punctuation, or additional text
4. If unsure, respond with "default"
"""
    handler = MultiGraph(
        classifier=Graph(
            id='classifier',
            system_prompt=classifier_system_prompt,
            retry_prompt='retry classification',
            converter_agent=common_converter,
            validator_agent=classifier_validator,
            router_agent=common_router,
            ollama_model='llama3',
            openai_model=''),
        default=Graph(
            id='default',
            system_prompt='answer the chat',
            retry_prompt='retry to answer',
            converter_agent=common_converter,
            validator_agent=common_validator,
            router_agent=common_router,
            ollama_model='gemma3',
            openai_model=''),
        gherkin=Graph(
            system_prompt=f"You are to text-to-gherkin converter, try to convert user query to valid gherkin.",
            retry_prompt=f"retry conversion",
            converter_agent=gherkin_converter,
            validator_agent=gherkin_validator,
            router_agent=gherkin_router,
            ollama_model='gemma3'),
        search=Graph(
            id='search',
            system_prompt='You are a chatbot which makes a web search for latest data and answer user query based on web content',
            retry_prompt='Retry to make a web search again for latest data and answer user query based on web content',
            converter_agent=search_converter,
            validator_agent=common_validator,
            router_agent=common_router,
            ollama_model='gemma3',
            openai_model=''),
    )
    print(handler.run('get gherkin for stocks in nifty 50 which have close > ema 10'))
    # draw_graph(handler, "graph.png")
