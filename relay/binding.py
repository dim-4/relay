from pydantic import BaseModel
from typing import Any, Callable, Optional
from .consts import DEFAULT_CHANNEL, DEFAULT_EVENT_TYPE
from .event import Event, SourceInfo


class Binding(BaseModel): ...


class Subscription(Binding):
    handler:Callable[..., Any] = ...
    event_type:Optional[str] = DEFAULT_EVENT_TYPE
    channel:Optional[str] = DEFAULT_CHANNEL
    source:Optional[SourceInfo] = None


class Emission(Binding):
    emitter:Callable[..., Any] = ...
    event_type:Optional[str] = DEFAULT_EVENT_TYPE
    channel:Optional[str] = DEFAULT_CHANNEL
