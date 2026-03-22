from pytick.llm.llm_types import State
from langchain_core.language_models.chat_models import BaseChatModel


def validator_agent(state: State, llm: BaseChatModel) -> State:
    """Chat validator will just validate the llm reply"""
    if not state.get("messages", []):
        return state

    ai_message = None
    for msg in state.get("messages", []):
        if hasattr(msg, "type") and msg.type == "ai":
            ai_message = msg.content
            break

    if not ai_message:
        return State(
            message_type="invalid",
            errors=["No content found"]
        )
    return State(
        message_type="valid",
        errors=[]
    )
