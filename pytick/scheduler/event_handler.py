from collections.abc import Callable

class EventType:
    TABLES_UPDATED = "TABLES_UPDATED"

class EventHandler:
    """
    Registry of event listeners keyed by event name.

    Attributes:
        listeners (dict[str, list[Callable[[str], None]]]): Map of event name
            to subscribed callbacks.
    """

    def __init__(self):
        """Initializes an EventHandler instance."""
        self.listeners = {}

    def subscribe(self, event:str, action: Callable[[str], None]):
        """Subscribes a new action to the event."""
        if event in self.listeners:
            self.listeners[event].append(action)
        else:
            self.listeners[event] = [action]

    def unsubscribe(self, event:str, action: Callable[[str], None]):
        """Unsubscribes an action from the event."""
        if event in self.listeners and action in self.listeners[event]:
            self.listeners[event].remove(action)
            if not self.listeners[event]:
                del self.listeners[event]

    def notify(self, event:str):
        """Notifies all subscribed listeners of the event."""
        for action in self.listeners.get(event, []):
            action(event)
