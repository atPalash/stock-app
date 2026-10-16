from collections.abc import Callable
from enum import Enum


class EventType(Enum):
    TABLES_UPDATED = "TABLES_UPDATED"


class EventHandler:
    """
    Registry of event listeners keyed by event name.

    Attributes:
        listeners (dict[EventType, list[Callable[[EventType, str], None]]]):
            Map of event type to subscribed callbacks.
    """

    def __init__(self):
        """Initializes an EventHandler instance."""
        self.listeners: dict[EventType, list[Callable[[EventType, str], None]]] = {}

    def subscribe(self, event: EventType, action: Callable[[EventType, str], None]):
        """Subscribes a new action to the event."""
        if event in self.listeners:
            if action not in self.listeners[event]:
                self.listeners[event].append(action)
        else:
            self.listeners[event] = [action]

    def unsubscribe(self, event: EventType, action: Callable[[EventType, str], None]):
        """Unsubscribes an action from the event."""
        if event in self.listeners and action in self.listeners[event]:
            self.listeners[event].remove(action)
            if not self.listeners[event]:
                del self.listeners[event]

    def notify(self, event: EventType, data: str):
        """Notifies all subscribed listeners of the event."""
        for action in self.listeners.get(event, []):
            action(event, data)
