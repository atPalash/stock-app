from pytick.llm.llm_types import State


def router(state: State) -> State:
    """Route the message to the appropriate agent based on the classification."""
    if state.get('retry_count', 0) >= 4:  # Max 4 retries
        return State(
            message_type="max_retries",
        )
    return state
