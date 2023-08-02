""" testing @listens decorator inside the Relay class """
import pytest

from pydantic import BaseModel
from relay.event import Event
from relay.relay import Relay

MAGENTA = "\033[35m"; RESET = "\033[0m"


def test_listens_without_event_parameter():
    """ Test `listens` decorator's behavior without an 'event' parameter. """
    with pytest.raises(TypeError):
        @Relay.listens
        def some_function_without_event(param1: str):
            pass

def test_listens_with_incorrect_event_type():
    """ Test `listens` decorator handling of wrong 'event' type hint. """
    with pytest.raises(TypeError):
        @Relay.listens
        def some_function_with_wrong_event_type(event:str):
            pass


class SomeModel(BaseModel):
    message: str


class DummyRelay(Relay):

    @Relay.listens
    def some_method_with_event(self, event: Event[SomeModel]):
        return event.data.message
    
    @Relay.listens
    def method_with_no_event_type(self, event:Event):
        return event.data


def test_listens_data_validation():
    """Test @listens decorator for event data type validation."""
    relay_instance = DummyRelay()

    # valid because some_method_with_event expects an Event[SomeModel]
    valid_event = Event(data=SomeModel(message="Valid"))
    assert relay_instance.some_method_with_event(valid_event) == "Valid"

    # invalid because some_method_with_event expects an Event[SomeModel]
    invalid_event = Event(data={"not_a_message": "Invalid"})
    with pytest.raises(TypeError):
        relay_instance.some_method_with_event(invalid_event)
    
    try:
        relay_instance.some_method_with_event(invalid_event)
    except TypeError as e:
        print(f"{MAGENTA}{e}{RESET}")
        assert str(e) == (f"Event data: -> {invalid_event.data} <- "
                          f"of type {type(invalid_event.data)} "
                          f"does not match the inferred type {SomeModel} "
                          f"hinted to the decorated method "
                          f"'{relay_instance.some_method_with_event.__name__}"
                          "(self, event:Event[T])'.")

def test_listens_no_data_validation():
    """Test @listens decorator when no type hint is provided for event."""
    relay_instance = DummyRelay()

    # Test with a variety of data types since there's no specific 
    # type to validate against
    test_data = [
        SomeModel(message="Valid"),
        {"not_a_message": "Invalid"},
        "random_string",
        12345,
        [1, 2, 3, 4],
        (5, 6, 7, 8),
        None
    ]
    for data in test_data:
        event = Event(data=data)
        assert relay_instance.method_with_no_event_type(event) == data

def test_listens_outside_relay():
    """ Test `listens` decorator's behavior when used outside of `Relay` 
        derived classes. 
    """
    class NotARelay:
        @Relay.listens
        def some_method(self, event: Event[SomeModel]):
            return event.data.message

    instance = NotARelay()

    with pytest.raises(TypeError):
        instance.some_method(Event(data=SomeModel(message="Test")))
