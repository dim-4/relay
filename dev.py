import inspect
from collections import abc
from pydantic import BaseModel, ValidationError
from time import time
from typing import Generic, TypeVar, Any, get_args, get_origin, Literal, Callable, Union
import types

T = TypeVar('T', bound=Any)
class Event(Generic[T]):
    def __init__(self, data:T) -> None:
        self.data:T = data
        self.time = time()


def truncate(data: Any, length: int = 20) -> str:
    """
    Truncate the string representation of data if it's longer than the specified length.
    Append "..." to the end of the truncated string.

    Args:
    - data (Any): The data to truncate.
    - length (int, optional): The maximum length of the string representation. Defaults to 20.

    Returns:
    - str: The truncated string representation of the data.
    """
    data_repr = str(data)
    return data_repr if len(data_repr) <= length else data_repr[:length] + "..."

def type_check(value, type_hint:BaseModel|Any):
    # If the type_hint is a subclass of BaseModel, use Pydantic's validation
    if issubclass(type(type_hint), BaseModel):
        try:
            type_hint.parse_obj(value)
            return True
        except ValidationError:
            return False

    origin = get_origin(type_hint)
    # print("ORIGIN --> ", origin)

    # For non-generic types, which includes basic types like int, str, etc., and user-defined classes.
    if not origin:
        return isinstance(value, type_hint)

    # Handle List[type] or List[List[type]] and so on
    if origin == list:
        args = get_args(type_hint)
        return isinstance(value, list) and all(type_check(item, args[0]) for item in value)
    
    # Handle Tuple[type] or Tuple[Tuple[type]] and so on
    if origin == tuple:
        args = get_args(type_hint)
        return isinstance(value, tuple) and all(type_check(item, args[0]) for item in value)
    
    # Handle Set[type] or Set[Set[type]] and so on
    if origin == set:
        args = get_args(type_hint)
        return isinstance(value, set) and all(type_check(item, args[0]) for item in value)

    # Handle Dict[key_type, val_type] or Dict[key_type, Dict[key_type, val_type]] and so on
    if origin == dict:
        key_type, val_type = get_args(type_hint)
        return isinstance(value, dict) and all(isinstance(k, key_type) and type_check(v, val_type) for k, v in value.items())

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
        raise NotImplementedError("Callable type hints with parameters are not supported yet.")

    # Add more complex type checks as needed

    allowed_types = [list, tuple, set, dict]
    if type(type_hint) not in allowed_types:
        raise TypeError(f"Type '{type_hint}' is not on of allowed in the type hints - combinations of: BaseModel, [int, str, ...] or {allowed_types} or user defined classes.")

    return False

def receives(func):
    params = inspect.signature(func).parameters
    if 'event' not in params:
        raise TypeError(f"The function '{func.__name__}' must have an 'event' parameter for the '@receives' decorator to work.")

    annotations = params['event'].annotation
    origin = get_origin(annotations)
    if origin is not None and origin is not Event:
        raise TypeError("The @receives decorator can only be applied to functions with Event as their parameter type.")
    
    # Get the actual data schema from the annotation
    event_args = get_args(annotations)
    event_schema:BaseModel = None
    if event_args:  # assumes first annotated argument is the event schema
        event_schema = event_args[0]
    
    def wrapper(event: Event[Any], *args, **kwargs):
        if not type_check(event.data, event_schema):
            data_truncated = truncate(event.data)
            raise TypeError(f"Event data: -> {data_truncated} <- does not match the expected type {event_schema}")
        return func(event, *args, **kwargs)
    return wrapper

# ---
class Dummy2: ...
class Dummy(Dummy2):
    def __init__(self) -> None:
        pass


class AudioMetadata(BaseModel):
    name: str
    year: int

class Audio(BaseModel):
    audio: str
    metadata: AudioMetadata

# @receives
# def on_audio(event:Event[Audio]):
#     print(event.data.audio)
#     print(event.data.metadata)

# audio = Audio(audio=b"123x\5", metadata=AudioMetadata(name="song", year=2021))
# event = Event(audio)
# on_audio(event)


# @receives
# def on_int(event:Event[int]):
#     print(event.data)
# event = Event(1)
# on_int(event)


# @receives
# def on_nested_data(event:Event[dict[str, list[int]]]):
#     print(event.data)
# event = Event({"a": [1, 2, 3]})  # {"a": [1, 2, 3, '4']} -> ValueError
# on_nested_data(event)


# @receives
# def on_nested_data2(event:Event[tuple[str]]):
#     print(event.data)
# event = Event(("a", "b", "c"))  # ("a", "b", 1) -> TypeError
# on_nested_data2(event)


# @receives
# def on_nested_data3(event:Event[set[int]]):
#     print(event.data)
# event = Event({1, 2, 3})  # {1, 2, 3, '4'} -> TypeError
# on_nested_data3(event)


# dummy = Dummy()
# @receives
# def on_dummy_new_union(event:Event[Dummy|None]):
#     print(event.data)
# event = Event(None)
# on_dummy_new_union(event)


# @receives
# def on_union(event:Event[Union[int, str]]):
#     print(event.data)
# event = Event("x"*21)
# on_union(event)


# from queue import Queue
# @receives
# def on_deque(event:Event[Queue[int]]):
#     print(event.data)
# event = Event(Queue([1, 2, 3]))
# on_deque(event)


# from collections import deque
# @receives
# def on_deque(event:Event[deque[int]]):
#     print(event.data)
# event = Event(deque([1, 2, 3]))
# on_deque(event)


# @receives
# def on_literal(event:Event[Literal['a', 'b', 'c']]):
#     print(event.data)
# event = Event("x"*21)
# on_literal(event)


# @receives
# def on_callable(event:Event[Callable]):
#     print(event.data)
# event = Event(on_callable)
# on_callable(event)


""" used to manually test some functionalities """
from relay import Relay

""" NOTE

Event schema will be determined by looking at the methods in the
bindings that emit that event.
- Validation there would be to make sure all methods emitting same events
return the same data structure.

@receives([str, Audio, {str: int}])
def on_audio(self, event:Event): ...
- the validation happens in the decorator making sure that passed optional
data type parameter matches the type of the event it receives.


During the bindings initialization, we check:
1. All binded methods emitting the same event have the same return type.
2. All binded methods receiving events expect the same data type as the
return types of the methods emitting those events.
- this means we need to know the decorator params of the @receives decorator

"""

from time import time

# class Event:
#     def __init__(self, data) -> None:
#         self.data = data
#         self.time = time()

# def receives(event_schema=None):
#     def decorator(func):
#         def wrapper(*args, **kwargs):
#             result = func(*args, **kwargs)
#             return result
#         wrapper.event_schema = event_schema
#         return wrapper
#     return decorator

# from pydantic import BaseModel

# class Schema(BaseModel): ...

# class AudioMetadata(Schema):
#     name: str
#     year: int

# class Audio(Schema):
#     audio: str
#     metadata: AudioMetadata

# audio = Audio("", AudioMetadata(name="song", year=2021))

# @receives(Audio)
# def on_audio(event:Event):
#     print(event.data.audio)
#     print(event.data.metadata)

# ---

