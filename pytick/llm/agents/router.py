from pytick.llm.types import State


def router(state: State) -> State:
    """Route the message to the appropriate agent based on the classification."""
    message_type = state.get('message_type', "invalid")
    if message_type == "valid":
        return {**state, "next": "valid"}
    return {**state, "next": "invalid"}