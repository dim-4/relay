import inspect
from collections import defaultdict as dd
from pydantic import BaseModel
from typing import Any, Callable, Optional, TYPE_CHECKING
from .consts import DEFAULT_CHANNEL, DEFAULT_EVENT_TYPE
from .event import Event, SourceInfo

if TYPE_CHECKING:
    from .relay import Relay


class Binding(BaseModel):
    """Base class for event bindings."""
    method:Callable[..., Any] = ...
    event_type:Optional[str] = DEFAULT_EVENT_TYPE
    channel:Optional[str] = DEFAULT_CHANNEL


class Listener(Binding):
    """ TODO: docstring. use class level func for config """
    source:Optional[SourceInfo] = None


class Emitter(Binding):
    """ TODO: docstring. use class level func for config """


class Bindings:

    _by_chnl_and_type:dict[str, dict[str, list[Binding]]] = dd(lambda: dd(list))
    _by_relay:dict['Relay', list[Binding]] = dd(list)
    _by_function:dict[Callable[..., Any], list[Binding]] = dd(list)

    @classmethod
    def add(cls, binding:Binding):
        channel, event_type, func, instance = cls._get_binding_data(binding)
        
        b_chnl_and_type = cls._by_chnl_and_type[channel]
        if binding not in b_chnl_and_type[event_type]:
            b_chnl_and_type[event_type].append(binding)

        b_relay = cls._by_relay[instance]
        if binding not in b_relay:
            b_relay.append(binding)
        
        b_func = cls._by_function[func]
        if binding not in b_func:
            b_func.append(binding)

    @classmethod
    def remove(cls, binding:Binding):
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
        if binding in cls._by_function.get(func, []):
            cls._by_function[func].remove(binding)
            
        # Removing empty function
        if not cls._by_function.get(func):
            try:
                del cls._by_function[func]
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
    

    @staticmethod
    def _get_binding_data(binding:Binding):
        channel:str = binding.channel
        event_type:str = binding.event_type
        method:Callable = binding.method

        err_msg = "Binding method must come from Relay."
        if inspect.ismethod(method):
            # bound method of an instance
            instance = method.__self__
            if instance is None:
                raise ValueError(err_msg)
            # Checks if the method is bound to a class (i.e., @classmethod)
            if isinstance(instance, type):  
                # allow class methods marked as @classmethod
                pass  
        elif inspect.isfunction(method):
            # unbound function
            raise ValueError(err_msg)
        else:
            raise ValueError(err_msg)
        return channel, event_type, method, instance
