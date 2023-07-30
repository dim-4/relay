import inspect
import functools
from pydantic import BaseModel
from typing import Any, get_args, get_origin
from .event import Event
from .utils import type_check, truncate


class Relay:


    class NoEmit(BaseModel):
        """ tells @emits wrapper not to emit the event, just return the data """
        data: Any


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
                # NOTE: event.data will be validated against SomeModel
                # some logic here

            @receives
            def some_other_method(self, event: Event):
                # NOTE: event.data will not be validated
                # some other logic here
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
        def wrapper(self, event: Event[Any], *args, **kwargs):
            if not type_check(event.data, event_schema):
                data_truncated = truncate(event.data, 50)
                raise TypeError(f"Event data: -> {data_truncated} <- "
                                f"of type {type(event.data)} does not "
                                f"match the inferred type {event_schema} "
                                "hinted to the decorated method "
                                f"'{func.__name__}(self, event:Event[T])'.")
            return func(self, event, *args, **kwargs)
        return wrapper
