from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from typing import Annotated, Literal
from langgraph.graph.message import add_messages

class MessageClassifier(BaseModel):
    message_type: Literal["valid", "invalid"] = Field(..., description="Classify the message as valid or invalid.")

class State(TypedDict):
    messages: Annotated[list, add_messages]
    message_type: str | None
