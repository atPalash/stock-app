from pytick.llm.types import MessageClassifier, State
from langchain_core.language_models.chat_models import BaseChatModel

from pytick.query.query import QueryHandler


def validator_agent(state: State, llm: BaseChatModel) -> State:
    """Validate that the gherkin format follows the available step definitions."""
    if not state["messages"]:
        return state

    # Get the last assistant message (the generated Gherkin)
    last_message = None
    for msg in reversed(state["messages"]):
        if hasattr(msg, "type") and msg.type == "ai":
            last_message = msg.content
            break

    if not last_message:
        return {
            **state,
            "message_type": "invalid",
            "validation_errors": ["No Gherkin content found"],
        }

    # Now validate against step patterns
    is_valid, _, errors = QueryHandler.parse_gherkin(last_message)
    if is_valid:
        return {**state, "message_type": "valid"}
    else:
        return {**state, "message_type": "invalid", "validation_errors": errors}
