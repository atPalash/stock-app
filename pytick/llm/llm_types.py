from typing_extensions import TypedDict
from typing import Literal


class State(TypedDict, total=False):
    messages: list
    message_type: Literal["chat", "gherkin", "valid", "invalid", "max_retries"]
    errors: list
    retry_count: int
    system_prompt: str
    retry_prompt: str
