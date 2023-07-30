from collections import abc
from pydantic import BaseModel, ValidationError
from types import UnionType
from typing import Any, Callable, get_args, get_origin, Literal, Union


def truncate(data: Any, length: int = 20) -> str:
    """
    Truncate the string representation of data if it's longer than the 
    specified length. Append "..." to the end of the truncated string. 
    If the data starts with an opening brace, append the matching closing 
    brace after "...".
    
    Args:
    ----
    - `data` (`Any`): The data to truncate.
    - `length` (`int`, `optional`): The maximum length of the string 
      representation. Defaults to 20.

    Returns:
    -------
    str
        The truncated string representation of the data.
    """
    data_repr = str(data)
    matches = {"{": "}", "[": "]", "(": ")", "<": ">"}
    end = "..."
    
    if len(data_repr) > length:
        # If data starts with an opening brace, update the ending to include the matching closing brace.
        if data_repr[0] in matches:
            end += matches[data_repr[0]]
        return f"{data_repr[:length-len(end)]}{end}"
    else:
        return data_repr

def type_check(value, type_hint:BaseModel|Any):
    """
    Checks if the given value matches the expected type hint.

    This function is designed to handle a wide variety of type hints, 
    including those from the `typing` module, Pydantic's BaseModel, and 
    other base types. For Pydantic's BaseModel subclasses, the function 
    leverages Pydantic's internal validation to determine type compatibility.

    Parameters:
    ----------
    - value (Any): The value to be type-checked.
    - type_hint (BaseModel|Any): The expected type hint for the value. 
      This can be a basic type like int or str, a subclass of BaseModel, or 
      a more complex type hint from the `typing` module such as List[int] 
      or Union[str, int].

    Returns:
    -------
    - bool: True if the value matches the type hint, False otherwise.

    Supported type hints include:
    - Basic Python types: int, str, float, etc.
    - Pydantic's BaseModel subclasses.
    - User defined classes.
    - Typing constructs: Union, Literal.
    - May be extended to support more complex type hints in the future.

    Notes:
    -----
    - When checking against Pydantic's BaseModel, the function attempts to
      parse the value using the model's `parse_obj` method. If successful, the 
      value matches the type hint.
    - For Callable type hints, only unparameterized checks (e.g., `Callable`) 
      are supported. Parameterized versions (e.g., `Callable[[int, str], bool]`) 
      are not yet implemented.

    Raises:
    ------
    - ValidationError: If the value does not match a BaseModel type hint.
    - TypeError: If the provided type hint is not supported.
    - NotImplementedError: If the function encounters an unsupported 
      parameterized Callable type hint.
    """
    # If the type_hint is a subclass of BaseModel, use Pydantic's validation
    if issubclass(type(type_hint), BaseModel):
        try:
            type_hint.parse_obj(value)
            return True
        except ValidationError:
            return False

    origin = get_origin(type_hint)

    # for basic types (int, str, etc.) and user-defined classes
    if not origin:
        return isinstance(value, type_hint)

    # Handle List[type] or List[List[type]] and so on
    if origin == list:
        args = get_args(type_hint)
        return (isinstance(value, list) and 
                all(type_check(item, args[0]) for item in value))
    
    # Handle Tuple[type] or Tuple[Tuple[type]] and so on
    if origin == tuple:
        args = get_args(type_hint)
        return (isinstance(value, tuple) and
                all(type_check(item, args[0]) for item in value))
    
    # Handle Set[type] or Set[Set[type]] and so on
    if origin == set:
        args = get_args(type_hint)
        return (isinstance(value, set) and 
                all(type_check(item, args[0]) for item in value))

    # Handle Dict[key_type, val_type] and so on
    if origin == dict:
        key_type, val_type = get_args(type_hint)
        return (isinstance(value, dict) and 
                all(isinstance(k, key_type) and 
                    type_check(v, val_type) for k, v in value.items()))

    # Handle Union types (which includes Optional)
    if origin is types.UnionType or origin is Union:
        allowed_types = get_args(type_hint)
        return any(type_check(value, t) for t in allowed_types)

    # Handle Literal types
    if origin == Literal:
        allowed_values = get_args(type_hint)
        return value in allowed_values

    # Handle Callable types
    if origin == abc.Callable:
        args = get_args(type_hint)
        # Check if Callable is parameterized i.e. Callable[[int, str], bool]
        if args == ():
            return callable(value)
        raise NotImplementedError("Callable type hints with parameters "
                                  "(ex: Callable[[int, str], bool]) "
                                  "are not supported yet.")

    # Add more complex type checks as needed

    raise TypeError(f"Type '{type_hint}' is not supported.")
    # return False



from __future__ import annotations
from time import time
from pydantic import BaseModel, Field
from typing import (Any, Callable, Generic, NamedTuple, 
                    Optional, TYPE_CHECKING, TypeVar)
from .constants import DEFAULT_CHANNEL, DEFAULT_EVENT_TYPE
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


import inspect
import functools
from pydantic import BaseModel
from typing import Any, get_args, get_origin
from .event import Event
from .utils import type_check, truncate


class Relay:
    pass

    @classmethod
    def receives(cls, func):
        """
        Decorator that validates the data of an `Event` parameter passed 
        to the decorated method.

        The `@receives` decorator is intended for methods that have a 
        parameter named 'event', which should be an instance of the 
        `Event` class. This decorator will validate the data contained 
        within the `Event` against the specified type hint.

        The schema or type is inferred from the type hint of the 'event' 
        parameter. For instance, if the method signature is 
        `def method_name(event: Event[SomeModel])` or `Event[int|str]` or 
        `Event[Union[str, int]]`, the data inside `event` will be 
        validated against the respective type hint.

        If the `event` parameter's type hint doesn't include a specific 
        type (e.g., `Event` without `[SomeType]`), the event data won't 
        be validated.

        If the data does not match the expected type or schema, a 
        `TypeError` is raised.

        Parameters:
        ----------
        - `func (Callable)`: The method to be decorated. Must have a 
        parameter named 'event'.

        Returns:
        -------
        - `Callable`: The wrapped function that includes data validation.

        Raises:
        ------
        - `TypeError`: If the 'event' parameter is missing from the method 
        or if the method's type hint for 'event' is not of type `Event`.
        - Other exceptions may be raised if internal validation crashes.

        Example:
        --------
        ```python
        class SomeRelay(Relay):

            @receives
            def some_method(self, event: Event[SomeModel]):
                # some logic here
        ```

        Note:
        ----
        - The decorated method must have an 'event' parameter, and the type hint
        for this parameter should be `Event` with an appropriate type or schema.
        """
        params = inspect.signature(func).parameters
        if 'event' not in params:
            raise TypeError(f"The method '{func.__name__}' must have an 'event'"
                            " parameter for the '@receives' decorator to work.")

        annotations = params['event'].annotation
        origin = get_origin(annotations)
        if origin is not Event:
            raise TypeError("The @receives decorator can only be applied to "
                            "methods with `Event` as their parameter type.")
        
        # Get the actual data schema from the annotation
        event_args = get_args(annotations)
        event_schema:BaseModel = None
        if event_args:  # assumes first annotated argument is the event schema
            event_schema = event_args[0]
        
        @functools.wraps(func)  # preserve func metadata
        def wrapper(self, event: Event[Any], *args, **kwargs):
            if not type_check(event.data, event_schema):
                data_truncated = truncate(event.data)
                raise TypeError(f"Event data: -> {data_truncated} <- does not "
                                f"match the expected type {event_schema}")
            return func(self, event, *args, **kwargs)
        return wrapper

