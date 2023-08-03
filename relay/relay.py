import asyncio
import inspect
import functools
import logging
from pydantic import BaseModel
from typing import Any, get_args, get_origin
from .bindings import Bindings, Listener, Emitter, Binding
from .event import Event, SourceInfo
from .utils import type_check, truncate

logging.basicConfig(level=logging.DEBUG,
                    format=('[%(levelname)s] [%(asctime)s] '
                            '[%(module)s:%(lineno)d] %(message)s'),
                    datefmt='%Y-%m-%d %H-%M-%S')
logger = logging.getLogger(__name__)
RED = "\033[1;31m"; MAGENTA = "\033[1;35m"; GREEN = "\033[1;32m"
RST = "\033[0;0m"

class Relay:

    class NoEmit(BaseModel):
        """ tells @emits wrapper not to emit the event, just return the data """
        data: Any

    @classmethod
    async def emit(cls, event:Event):
        """
        IMPORTANT:
        ---------
        You should `await` this method to ensure that the 
        asynchronous tasks it spawns (for notifying listeners) are scheduled 
        properly.

        Asynchronously emits a given event to all compatible listeners 
        registered with the `Bindings` class.

        This method propagates the provided event to all the listener methods 
        which are registered for the event's `channel` and `event_type`.
        However, if some listeners expect events from a particular source,
        the event source will be checked before delivering to them. 

        Listeners will receive the event asynchronously, and any exceptions 
        raised by the listeners are caught and logged, ensuring that one 
        listener's exception will not halt the distribution of the event to 
        other listeners.

        Parameters:
        ----------
        - `event (Event[Any])`: The event instance containing the data to be 
        emitted. This should include information like `channel`, `event_type`, 
        and the source of the event optionally.

        Usage:
        -----
        ```python
        # Example to emit an event
        event = Event(data="Hello, World!", 
                      channel="greetings", 
                      event_type="hello")
        await Relay.emit(event)
        ```

        Note:
        ----
        - It's essential that the `Bindings` class has been populated with the 
        necessary listeners for the event to be effectively delivered.
        - If listeners have source restrictions specified, it's crucial that the 
        `event` parameter contains accurate source information.
        - For best practices, always `await` this method, even though not doing 
        so might work in some scenarios.

        Returns:
        -------
        None. However, side effects include calling all the compatible listener 
        methods with the provided event.
        """
        def source_compatible(s_event:SourceInfo, 
                              s_listener:SourceInfo) -> bool:
            """ returns True if event source if compatible with listener
                source (that is, if listener is expecting an event only
                from a specific source) 
            """
            listn_relay = None if s_listener is None else s_listener.relay
            listn_emitter = None if s_listener is None else s_listener.emitter
            event_relay = None if s_event is None else s_event.relay
            event_emitter = None if s_event is None else s_event.emitter

            if listn_relay != None and event_relay != listn_relay:
                return False
            if listn_emitter != None and event_emitter != listn_emitter:
                return False
            return True

        async def safe_method(event, method):
            """ async call the bound method, catch any exceptions """
            try:
                result = await method(event)
            except Exception as e:
                logger.exception(f"{RED}Exception in executing emission: {e}. "
                                 f"Event: <{event}>, Method: <{method}>{RST}")

        listeners:list[Listener] = Bindings.get_by_event(event.channel, 
                                                         event.event_type,
                                                         filter_=Listener)

        for listener in listeners:
            if not source_compatible(event.source, listener.source):
                continue
            method = listener.method
            asyncio.create_task(safe_method(event, method))
    
    @classmethod
    def emits(cls, func):
        """
        A class method decorator that allows methods within a `Relay` or its 
        child class to emit events with data validation against the provided 
        type hints. It ensures that methods are asynchronous and their return 
        type matches the expected event's payload type.

        This decorator performs two types of checks:
        1. **Static Checks** - Checks that:
            - a. The decorated method is asynchronous.
            - b. The method has a return type hint.
        2. **Dynamic Checks** - Checks that:
            - a. The method belongs to a class inheriting from `Relay`.
            - b. The actual returned data matches the type hint.

        If a method returns an instance of `NoEmit`, the event emission is 
        bypassed, and only the data contained within is returned.

        Parameters:
        ----------
        - `func (Callable)`: The method to be decorated.

        Returns:
        -------
        - `Callable`: The wrapped function that includes event emission logic.

        Raises:
        ------
        - `TypeError`: If the method does not meet the criteria specified above.

        Example:
        --------
        ```python
        class CustomRelay(Relay):
            
            @emits
            async def some_method(self, arg1) -> SomeDataType:
                # some logic...
                return some_data  # This data will be emitted as event payload
        ```

        Note:
        ----
        - The decorated method must belong to a class that either is or 
        inherits from `Relay`.
        - For conditional event emission, the method can return an instance 
        of `NoEmit` to skip the emission but still validate the data type.
        - Bindings to this method are found in `Bindings` class.
        """
        # STATIC CHECK 
        # make sure that the decorated method is a coroutine
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(
                f"The method '{func.__name__}' must be asynchronous. The "
                f"'@emits' decorator can only be applied to async methods.")

        # get the return type hint
        signature = inspect.signature(func)
        ret_annotation = signature.return_annotation
        
        # Ensure an explicit return type is provided
        if ret_annotation is inspect.Signature.empty:
            raise TypeError(
                f"The method '{func.__name__}' that is decorated by "
                "@Relay.emits, must have an explicit return type "
                "hint. For example, 'def method_name() -> str:'. If "
                "the method does not return anything, use '-> None'. "
                "If the method can return anything, use '-> typing.Any'.")

        
        @functools.wraps(func)  # preserve func metadata
        async def wrapper(self, *args, **kwargs):
            # DYNAMIC CHECK
            # make sure that self is an instance of Relay or its children
            if not isinstance(self, Relay):
                raise TypeError(
                    f"The method '{func.__name__}' that is decorated by "
                    "@Relay.emits, must be a method of a class that "
                    "inherits from Relay.")

            result = await func(self, *args, **kwargs)

            # If the return type hint is `NoEmit`, don't emit the event
            no_emit = isinstance(result, cls.NoEmit)

            data = result.data if no_emit else result
            if not type_check(data, ret_annotation):
                data_truncated = truncate(data, 50)
                raise TypeError(
                    f"Return value: -> {data_truncated} <- of type "
                    f"{type(data)} does not match the inferred type "
                    f"{ret_annotation} hinted to the decorated method "
                    f"'{func.__name__}(self, ...)'.")
                    
            if no_emit:
                return result.data
            
            # emit
            method = getattr(self, func.__name__)
            emitters = Bindings.get_by_method(method, filter_=Emitter)

            for emitter in emitters:
                await cls.emit(
                    Event(data=result, channel=emitter.channel,
                          event_type=emitter.event_type,
                          source=SourceInfo(relay=self, emitter=method)))

            return result
        return wrapper

    @classmethod
    def listens(cls, func):
        """
        Decorator that validates the data of an `Event` parameter passed 
        to the decorated method.

        1. Statically - Makes sure the decorated method has `event:Event[T]`
        or `event:Event` as a parameter.
        2. Dynamically - Validates the data of the received event against
        the type hint in the method signature.

        The `@receives` decorator is intended for methods that have a 
        parameter named 'event', which should be an instance of the 
        `Event` class. This decorator will validate the data contained 
        within the `Event` against the specified type hint.

        The schema or type is inferred from the type hint of the 'event' 
        parameter. For instance, if the method signature is 
        `def method_name(event: Event[SomeModel])` or `Event[int|str]` or 
        `Event[Union[str, int]]`, etc. the data inside `event` will be 
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
                # NOTE: event.data will be validated against SomeModel
                # some logic here

            @receives
            def some_other_method(self, event: Event):
                # NOTE: same as Event[Any] - event.data will not be validated
                # some logic here
        ```

        Note:
        ----
        - The decorated method must belong to a class that either is or 
        inherits from `Relay`.
        - The decorated method must have an 'event' parameter, and the type hint 
        for this parameter should be `Event` with an appropriate type or schema.
        """
        # STATIC CHECK
        # make sure that the decorated method is a coroutine
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(
                f"The method '{func.__name__}' must be asynchronous. The "
                f"'@listens' decorator can only be applied to async methods.")

        params = inspect.signature(func).parameters
        if 'event' not in params:
            raise TypeError(f"The method '{func.__name__}' must have an 'event'"
                            " parameter for the '@receives' decorator to work.")

        annotation = params['event'].annotation
        # If the annotation is just `Event` without a type hint, set it to Any
        if annotation is Event:
            annotation = Event[Any]
        origin = get_origin(annotation)
        if origin is not Event:
            raise TypeError("The @receives decorator can only be applied to "
                            "methods with `Event` as their parameter type.")
        
        # Get the actual data schema from the annotation
        event_args = get_args(annotation)
        event_schema:BaseModel = None
        if event_args:  # assumes first annotated argument is the event schema
            event_schema = event_args[0]
        
        @functools.wraps(func)  # preserve func metadata
        async def wrapper(self, event: Event[Any], *args, **kwargs):
            # DYNAMIC CHECK
            # make sure that self is an instance of Relay or its children
            if not isinstance(self, Relay):
                raise TypeError(
                    f"The method '{func.__name__}' that is decorated by "
                    "@Relay.receives, must be a method of a class that "
                    "inherits from Relay.")

            if not type_check(event.data, event_schema):
                data_truncated = truncate(event.data, 50)
                raise TypeError(
                    f"Event data: -> {data_truncated} <- of type "
                    f"{type(event.data)} does not match the inferred type "
                    f"{event_schema} hinted to the decorated method "
                    f"'{func.__name__}(self, event:Event[T])'.")
            return await func(self, event, *args, **kwargs)
        return wrapper
    

    # Binding methods - these methods are used to add/remove bindings

    def remove_binding_relay(self):
        """
        Removes all bindings associated with a specific relay.

        Parameters:
        ----------
        - `self (Relay)`: The relay whose bindings are to be removed.
        """
        Bindings.remove_relay(self)

    @classmethod
    def add_binding(cls, binding: Emitter | Listener):
        """
        Adds a binding to the `Bindings` class.

        Parameters:
        ----------
        - `binding (Binding)`: The binding to be added. (Listener or Emitter)

        Raises:
        ------
        - `ValueError`: If the binding's method does not belong to a class 
        inheriting from `Relay`.
        """
        Bindings.add(binding)
    
    @classmethod
    def remove_binding(cls, binding: Emitter | Listener):
        """
        Removes a binding from the `Bindings` class.

        Parameters:
        ----------
        - `binding (Binding)`: The binding to be removed. (Listener or Emitter)
        """
        Bindings.remove(binding)
