import logging
from pytick.llm.llm_types import State
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from pytick.llm.utility import extract_gherkin
from pytick.query.steps import StepData
from pytick.utility.utility import get_logger

logger = get_logger(__file__, logging.DEBUG)


def converter_agent(state: State, llm: BaseChatModel) -> State:
    """Convert input messages to Gherkin format using available step definitions."""
    messages = state.get('messages', [])
    retry_count = state.get("retry_count", 0)
    if retry_count == 0:
        system_msg = SystemMessage(content=state.get('system_prompt', ''))
        user_input = None
        for msg in messages:
            if hasattr(msg, 'type') and msg.type == 'human':
                user_input = msg
                break

        if not user_input:
            return state
        messages = [system_msg] + [user_input]
    elif retry_count > 0:
        retry_msg = SystemMessage(content=state.get('retry_prompt', ''))
        # Extract errors from state
        errors = state.get('errors', [])
        error_context = "\n".join(f"- {err}" for err in errors) if errors else "- No validator error provided"

        ai_message = ""
        user_query = ""
        # Use latest AI message and earliest human query for stable retry context.
        for msg in reversed(state.get("messages", [])):
            if hasattr(msg, "type") and msg.type == "ai":
                ai_message = msg.content
                break
        for msg in state.get("messages", []):
            if hasattr(msg, "type") and msg.type == "human":
                user_query = msg.content
                break

        retry_context = (
            "Repair the previous Gherkin using the validator errors.\n"
            "Do not change the original intent/query. Keep valid lines as-is.\n"
            "Only fix lines required to satisfy the regex validation errors.\n"
            "Return only the corrected Gherkin scenario.\n\n"
            f"Original user query:\n{user_query}\n\n"
            f"Previous AI Gherkin to fix:\n{ai_message}\n\n"
            f"Validator errors to fix:\n{error_context}"
        )
        messages = [retry_msg, HumanMessage(content=retry_context)]

    # Use the full conversation history for context
    reply = llm.invoke(messages)
    fetched_gherkin = extract_gherkin(reply.content)
    return State(
        messages=[AIMessage(content=fetched_gherkin)] + messages,
        message_type="valid",
        errors=[],
        retry_count=state.get("retry_count", 0) + 1
    )
