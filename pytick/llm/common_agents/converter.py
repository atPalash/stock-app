import logging
from pytick.llm.llm_types import State
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, SystemMessage

from pytick.utility.utility import get_logger

logger = get_logger(__file__, logging.DEBUG)


def converter_agent(state: State, llm: BaseChatModel) -> State:
    """Convert input messages to interactive reply."""
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
        messages = [system_msg, user_input]
    elif retry_count > 0:
        logger.warning(
            "Chat converter should just take the first reply from llm")

    # Use the full conversation history for context
    reply = llm.invoke(messages)
    return State(
        messages=[AIMessage(content=reply.content)] + messages,
        message_type="valid",
        errors=[],
        retry_count=state.get("retry_count", 0) + 1
    )
