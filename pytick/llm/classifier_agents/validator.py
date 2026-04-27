from pytick.llm.llm_types import State
from langchain_core.language_models.chat_models import BaseChatModel
from pytick.llm.common_agents.validator import validator_agent
from pytick.llm.utility import clean_llm_message
from langchain_core.messages import SystemMessage


def validator_agent(state: State, llm: BaseChatModel) -> State:
    """Chat validator will just validate the llm reply"""
    if not state.get("messages", []):
        return state

    ai_message = None
    system_message = None
    for msg in state.get("messages", []):
        if hasattr(msg, "type") and msg.type == "ai":
            ai_message = msg.content
            continue
        if hasattr(msg, "type") and msg.type == "system":
            system_message = msg.content
            continue

    if not ai_message:
        return State(
            message_type="invalid",
            errors=["No content found"]
        )
    ai_worker = clean_llm_message(ai_message)
    if system_message:
        # Add a simple check to see if the AI message contains any keywords from the system message
        valid_workers = []
        for line in system_message.splitlines():
            if line.startswith("VALID_WORKERS:"):
                for worker in line.split("VALID_WORKERS:")[1].strip().split(','):
                    valid_workers.append(clean_llm_message(worker))
                break
        if ai_worker not in valid_workers:
            return State(
                message_type="invalid",
                errors=["AI message does not align with system prompt"]
            )

    return State(
        messages=[SystemMessage(content=ai_worker), *
                  state.get("messages", [])],
        message_type="valid",
        errors=[]
    )
