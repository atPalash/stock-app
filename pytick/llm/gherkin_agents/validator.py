from langchain_core.messages import AIMessage, HumanMessage

from pytick.llm.llm_types import State
from langchain_core.language_models.chat_models import BaseChatModel

from pytick.query.query import QueryHandler


def validator_agent(state: State, llm: BaseChatModel) -> State:
    """Validate that the gherkin format follows the available step definitions."""
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
            errors=["No Gherkin content found"]
        )

    # Now validate against step patterns
    is_valid, _, errors = QueryHandler.parse_gherkin(ai_message)
    if is_valid:
        return State(
            message_type="valid",
            errors=[]
        )
    else:
        return State(
            message_type="invalid",
            errors=errors
        )
