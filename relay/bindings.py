import asyncio
import inspect
from collections import defaultdict as dd
from pydantic import BaseModel, field_validator
from typing import Any, Callable, Optional, TYPE_CHECKING
from .consts import DEFAULT_CHANNEL, DEFAULT_EVENT_TYPE, FORBIDDEN_CHARACTERS
from .event import Event, SourceInfo
from .utils import type_check, validate_forbidden_characters


if TYPE_CHECKING:
    from .relay import Relay


class Binding(BaseModel):
    """ Base class for event bindings. """
    method:Callable[..., Any] = ...
    event_type:Optional[str] = DEFAULT_EVENT_TYPE
    channel:Optional[str] = DEFAULT_CHANNEL

    @field_validator('channel', 'event_type', mode="before")
    def _check_forbidden_characters(cls, v:str) -> str:
        """
        Validate if the given value contains forbidden characters.
        
        Raises:
        ------
            ValueError: If forbidden characters are found in the value.
            
        Returns:
        -------
            The original value if no forbidden characters are found.
        """
        return validate_forbidden_characters(v, FORBIDDEN_CHARACTERS)
    
    @field_validator('method', mode="after")
    def _check_async(cls, func:Callable[..., Any]) -> Callable[..., Any]:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(
                f"The method must be asynchronous. Your method "
                f"'{func.__name__}' is synchronous. The Binding only "
                "supports asynchronous methods.")
        return func


class Listener(Binding):
    """
    A derived class from `Binding` that represents an event listener.
    
    This class is used to manage and encapsulate the event listener 
    configuration. It defines an event binding that listens to a 
    specific event type on a channel. The bound method will be invoked 
    when the event occurs.

    Class Attributes:
    ----------------
    `source` (Optional[SourceInfo]): Represents the source of the event. 
    It can be an instance of `SourceInfo`, used to provide additional 
    information about the source of the event. Default is `None`.
    
    Inherited Class Attributes:
    --------------------------
    `method` (Callable[..., Any]): The asynchronous callback method to be 
    invoked when the event occurs.

    `event_type` (Optional[str]): The type of event to listen for. 
    Default is the `DEFAULT_EVENT_TYPE`.

    `channel` (Optional[str]): The channel that the event will occur on. 
    Default is the `DEFAULT_CHANNEL`.

    Note:
    ----
    The event listener is tied to the method provided and must be an 
    asynchronous method. This is validated using the `check_async` 
    method inherited from `Binding`.
    """
    # TODO: docstring. use class level method for config
    source:Optional[SourceInfo] = None


class Emitter(Binding):
    """
    A class to represent event emission bindings.

    This class inherits from `Binding` and is designed to represent 
    configurations associated with emitting events. Events can be triggered 
    from a specific source to target receivers listening for them.

    Attributes:
    ----------
    method (Callable[..., Any]):
        The asynchronous method associated with the emitter. This is the 
        event generation mechanism. This method should be a coroutine.

    event_type (Optional[str], default=DEFAULT_EVENT_TYPE):
        The type of event being emitted. This helps in categorizing and 
        routing the emitted event to appropriate listeners.

    channel (Optional[str], default=DEFAULT_CHANNEL):
        The channel through which the event is emitted. Different channels
        may represent various logical groupings or pathways for events.

    Note:
    ----
    Emitter configurations should ensure valid channel and event type names
    by avoiding forbidden characters, and should only associate asynchronous
    methods for event emission.

    Examples:
    --------
    ```python
    emitter_instance = Emitter(method=async_emit_method,
                               event_type="custom_event",
                               channel="custom_channel")
    ```
    """
    # TODO: docstring. use class level method for config


class Bindings:
    """
    A class used to manage event bindings in a structured manner.

    This class contains static methods and properties that store the binding 
    data and allow manipulation of the binding instances (`Listener` or 
    `Emitter`). Each binding is registered under specific keys derived from 
    the binding data, including:
    1. Channel and Event type
    2. Associated Relay instance
    3. Method associated with the binding

    All bindings are internally managed using three dictionaries:
    `_by_chnl_and_type`, `_by_relay`, and `_by_method`, each representing 
    bindings by channel and event type, by relay instance, and by associated 
    method respectively. They contain same data indexed differently.

    Class Attributes:
    ----------------
    `_by_chnl_and_type`: A nested defaultdict that maps a channel (str) to 
    another defaultdict, which further maps an event type (str) to a list of 
    Binding instances.

    `_by_relay`: A defaultdict that maps a Relay instance to a list of Binding 
    instances.

    `_by_method`: A defaultdict that maps a method (Callable) to a list of 
    Binding instances.

    Methods:
    -------
    `clear() -> None:`
        Clear all registered bindings.

    `add(binding: Binding) -> None:`
        Add a new binding to the tracking structures.

    `remove(binding: Binding) -> None:`
        Remove a specific binding from the tracking structures.

    `remove_relay(relay: 'Relay') -> None:`
        Remove all bindings associated with a specific relay instance.

    `get_by_event(channel: str, event_type: str, filter_: Union[Binding, 
    Listener, Emitter]) -> list[Binding]:`
        Retrieve bindings based on channel and event_type patterns, optionally 
        filtered by binding type.

    `get_by_relay(relay: 'Relay', filter_: Union[Binding, Listener, Emitter])
    -> list[Binding]:`
        Retrieve bindings associated with a specific relay instance, 
        optionally filtered by binding type.

    `get_by_method(method: Callable[..., Any], filter_: Union[Binding, 
    Listener, Emitter]) -> list[Binding]:`
        Retrieve bindings associated with a specific method, 
        optionally filtered by binding type.
    """

    _by_chnl_and_type:dd[str, dd[str, list[Binding]]] = dd(lambda: dd(list))
    _by_relay:dd['Relay', list[Binding]] = dd(list)
    _by_method:dd[Callable[..., Any], list[Binding]] = dd(list)

    @classmethod
    def clear(cls):
        """ clears all bindings """
        cls._by_chnl_and_type.clear()
        cls._by_relay.clear()
        cls._by_method.clear()

    @classmethod
    def add(cls, binding:Binding):
        """
        Register a new event binding.

        This method stores the provided `binding` in internal tracking
        structures. 
        If the binding already exists, it is ignored. 

        Parameters:
        ----------
        - `binding` (Binding): The event binding instance to add.
        (`Listener` or `Emitter`)

        Note:
        ----
        Future iterations may introduce static type compatibility checks against
        other methods that this event channel is associated with. As of now, 
        dynamic type checking will be done when the event is emitted (against 
        emitter return type) and received (against expected Event type hint).
        These checks will only be done via `@Relay.emits` and `@Relay.receives`
        decorators inside `Relay` child classes.
        """
        channel, event_type, method, instance = cls._get_binding_data(binding)
        
        b_chnl_and_type = cls._by_chnl_and_type[channel]
        if binding not in b_chnl_and_type[event_type]:
            b_chnl_and_type[event_type].append(binding)

        b_relay = cls._by_relay[instance]
        if binding not in b_relay:
            b_relay.append(binding)
        
        b_func = cls._by_method[method]
        if binding not in b_func:
            b_func.append(binding)

    @classmethod
    def remove(cls, binding:Binding):
        """
        Remove a specified binding from internal tracking structures.
        
        This method cleans the binding references from `_by_chnl_and_type`,
        `_by_relay`, and `_by_method`. Additionally, it handles cleanup 
        of any empty nested dictionaries within these structures.

        Parameters:
        ----------
        - `binding` (Binding): The binding instance to be removed.

        Note:
        ----
        If a specified binding is not found, the method handles the removal 
        gracefully and ensures that empty references are cleaned up.
        """
        if binding is None:
            return
        
        channel, event_type, func, instance = cls._get_binding_data(binding)
        
        # Working with _by_chnl_and_type
        if binding in cls._by_chnl_and_type[channel].get(event_type, []):
            cls._by_chnl_and_type[channel][event_type].remove(binding)

        # Removing empty event type
        if not cls._by_chnl_and_type[channel].get(event_type):
            try:
                del cls._by_chnl_and_type[channel][event_type]
            except KeyError: pass

        # Removing empty channel
        if not cls._by_chnl_and_type[channel]:
            try:
                del cls._by_chnl_and_type[channel]
            except KeyError: pass

        # Working with _by_relay
        if binding in cls._by_relay.get(instance, []):
            cls._by_relay[instance].remove(binding)
            
        # Removing empty relay
        if not cls._by_relay.get(instance):
            try:
                del cls._by_relay[instance]
            except KeyError: pass

        # Working with _by_function
        if binding in cls._by_method.get(func, []):
            cls._by_method[func].remove(binding)
            
        # Removing empty function
        if not cls._by_method.get(func):
            try:
                del cls._by_method[func]
            except KeyError: pass

    @classmethod
    def remove_relay(cls, relay:'Relay'):
        """ removes all bindings associated with the relay """
        if relay is None:
            return
        if relay in cls._by_relay:
            bindings_to_remove = cls._by_relay[relay]
            for binding in bindings_to_remove:
                cls.remove(binding)

    @classmethod
    def get_by_event(cls, 
                    channel:str, 
                    event_type:str,
                    filter_:Binding|Listener|Emitter=Binding
    ) -> list[Binding]:
        """
        Retrieve bindings based on `channel` and `event_type` patterns.
        
        This method supports wildcard patterns in the `channel` and `event_type`
        arguments.
        The wildcard `'*'` can be used to represent zero or more characters.

        Examples:
        --------
            - `"channelA*"`: Matches any channel that starts with `"channelA"`.
            - `"*eventX"`: Matches any event type that ends with `"eventX"`.
            - `"ABC*def*xyz*123*"`: Matches channels that start with `"ABC"` and 
            contain the sequence `"def"`, `"xyz"`, `"123"`.

        Parameters:
        ----------
        - `channel` (str): The channel pattern to search.
        - `event_type` (str): The event type pattern to search.
        - `filter_` (Union[`Binding`, `Listener`, `Emitter`], optional): Filter 
        the results based on a particular binding type. Default is `Binding`.
        NOTE that `Listener` and `Emitter` are subclasses of `Binding`.

        Returns:
        -------
        - `list[Binding]`: A list of bindings that match the given patterns.

        Raises:
        ------
        - `TypeError`: If the provided filter_ doesn't match any of the
        expected types.
        """

        def _matches_pattern(s: str, pattern: str) -> bool:
            """Check if `s` matches the given pattern."""
            segments = pattern.split('*')
            
            # Check the first segment with startswith and the last segment 
            # with endswith for optimization
            if segments[0] and not s.startswith(segments[0]):
                return False
            if segments[-1] and not s.endswith(segments[-1]):
                return False
            
            start_idx = 0
            for segment in segments:
                # Find the current segment in the string starting from the 
                # last found index
                idx = s.find(segment, start_idx)
                if idx == -1:
                    return False
                # Move the pointer beyond the current found segment
                start_idx = idx + len(segment)
            
            return True

        def _retrieve_by_event(channel, event_type):
            # Base case: If both channel and event_type are specific
            # (non-wildcards and without pattern)
            if '*' not in channel and '*' not in event_type:
                return cls._by_chnl_and_type[channel][event_type]
            
            bindings = []

            # If the channel has a wildcard or pattern
            if '*' in channel:
                for ch in cls._by_chnl_and_type.keys():
                    if _matches_pattern(ch, channel):
                        bindings.extend(_retrieve_by_event(ch, event_type))
            # If the event_type has a wildcard or pattern
            elif '*' in event_type:
                for et in cls._by_chnl_and_type[channel].keys():
                    if _matches_pattern(et, event_type):
                        bindings.extend(_retrieve_by_event(channel, et))
            
            return bindings

        all_bindings = _retrieve_by_event(channel, event_type)

        # Filter based on the given filter.
        return [b for b in all_bindings if type_check(b, filter_)]

    @classmethod
    def get_by_relay(cls, 
                     relay:'Relay', 
                     filter_:Binding|Listener|Emitter=Binding
    ) -> list[Binding]:
        return [b for b in cls._by_relay[relay] if type_check(b, filter_)]
    
    @classmethod
    def get_by_method(cls, 
                      method:Callable[..., Any],
                      filter_:Binding|Listener|Emitter=Binding
    ) -> list[Binding]:
        return [b for b in cls._by_method[method] if type_check(b, filter_)]

    @staticmethod
    def _get_binding_data(binding:Binding):
        channel:str = binding.channel
        event_type:str = binding.event_type
        method:Callable = binding.method

        err_msg = "Binding method must come from Relay & must be bound (self)."
        if inspect.ismethod(method):
            # bound method of an instance
            instance = method.__self__
            if instance is None:
                raise ValueError(err_msg)
            # Checks if the method is bound to a class (i.e., @classmethod)
            if isinstance(instance, type):  
                # don't allow class methods marked as @classmethod
                raise ValueError(err_msg)
        elif inspect.isfunction(method):
            # unbound function
            raise ValueError(err_msg)
        else:
            raise ValueError(err_msg)
        return channel, event_type, method, instance
