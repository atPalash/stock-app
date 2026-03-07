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

    # Inject into system prompt
    system_prompt = state.get('system_prompt', '')
    system_msg = SystemMessage(content=system_prompt)

    # Find the last user message
    user_input = None
    for msg in messages:
        if hasattr(msg, 'type') and msg.type == 'human':
            user_input = msg
            break

    if not user_input:
        return state

    retry_count = state.get("retry_count", 0)
    messages = [system_msg] + [user_input]
    if retry_count > 0:
        # Extract errors from state
        errors = state.get('errors', [])
        error_context = ""
        if errors:
            error_context = f"\n\n⚠️ PREVIOUS ERRORS TO FIX:\n" + \
                "\n".join(f"- {err}" for err in errors)

        ai_message = None
        for msg in state.get("messages", []):
            if hasattr(msg, "type") and msg.type == "ai":
                ai_message = msg.content
                break
        ai_context = ""
        if ai_message:
            ai_context = f"\n\n💡 PREVIOUS AI SUGGESTION FIX THIS:\n{ai_message}"
        messages = [HumanMessage(
            content=ai_context + error_context)] + messages

    # Use the full conversation history for context
    reply = llm.invoke(messages)
    fetched_gherkin = extract_gherkin(reply.content)
    return State(
        messages=[AIMessage(content=fetched_gherkin)] + messages,
        message_type="valid",
        errors=[],
        retry_count=state.get("retry_count", 0) + 1
    )
