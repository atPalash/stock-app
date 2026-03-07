from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from typing import Literal


class MessageClassifier(BaseModel):
    message_type: Literal["valid", "invalid", "max_retries"] = Field(
        ..., description="Classify the message as valid or invalid.")


class State(TypedDict, total=False):
    messages: list
    message_type: str | None
    errors: list
    retry_count: int
    system_prompt: str
