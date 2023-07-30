from __future__ import annotations
from time import time
from pydantic import BaseModel, Field
from typing import (Any, Callable, Generic, NamedTuple, 
                    Optional, TYPE_CHECKING, TypeVar)
from .consts import DEFAULT_CHANNEL, DEFAULT_EVENT_TYPE
from .utils import truncate

if TYPE_CHECKING:
    from .relay import Relay
else:
    Relay = Any  # this is a hack but BaseModel won't validate anymore...


class SourceInfo(BaseModel):
    relay: Optional["Relay"] = None
    func: Optional[Callable] = None


T = TypeVar('T', bound=Any)

class Event(BaseModel, Generic[T]):
    """
    Represents a generic event with data of type `T`.

    This event encapsulates data payloads for communication between different
    parts of a system. Each event carries a type, a communication channel,
    source information, and a timestamp.

    Attributes:
    ----------
    - `data (T)`: The main payload or data for the event.
    - `channel (str)`: Communication channel for broadcasting.
    - `event_type (str)`: Type of the event for broadcasting.
    - `source (SourceInfo)`: Origin or source of the event (optional).
    - `time (float)`: Timestamp when the event was created.

    Constants:
    ---------
    - `DEFAULT (str)`: Default value for `event_type` and `channel`.

    Parameters:
    ----------
    - `data (T)`: The main payload or data for the event.
    - `event_type (str, optional)`: Type of the event. Defaults to 'DEFAULT'.
    - `channel (str, optional)`: Communication channel. Defaults to 'DEFAULT'.
    - `source (SourceInfo, optional)`: Source of the event. Defaults to None.

    Example:
    -------
    ```python
    event = Event(data={"message": "Hello!"}, 
                  event_type="GREETING", 
                  channel="MAIN",
                  source=SourceInfo(relay=my_relay_child, func=my_function))
    ```
    """
    data: T = ...
    channel: str = DEFAULT_CHANNEL
    event_type: str = DEFAULT_EVENT_TYPE
    source: Optional[SourceInfo] = None
    time: float = Field(default_factory=time)

    def __str__(self) -> str:
        """
        Return a user-friendly string representation of the Event instance.

        This method provides a readable representation of the Event instance,
        suitable for display to end-users or for logging purposes.

        Returns:
        -------
        `str`
            User-friendly representation of the Event instance.
        """
        data_repr = repr(self.data)
        channel_repr = repr(self.channel)
        event_type_repr = repr(self.event_type)
        source_repr = repr(self.source)
        time_repr = repr(self.time)

        return (f"Event(data={truncate(data_repr, 50)}, channel={channel_repr}, "
                f"event_type={event_type_repr}, source={source_repr}, "
                f"time={time_repr})")
