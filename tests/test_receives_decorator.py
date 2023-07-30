import pytest

from pydantic import BaseModel
from relay.event import Event
from relay.relay import Relay

MAGENTA = "\033[35m"; RESET = "\033[0m"


def test_receives_without_event_parameter():
    """ Test `receives` decorator's behavior without an 'event' parameter. """
    with pytest.raises(TypeError):
        @Relay.receives
        def some_function_without_event(param1: str):
            pass

def test_receives_with_incorrect_event_type():
    """ Test `receives` decorator handling of wrong 'event' type hint. """
    with pytest.raises(TypeError):
        @Relay.receives
        def some_function_with_wrong_event_type(event:str):
            pass


class SomeModel(BaseModel):
    message: str


class DummyRelay(Relay):

    @Relay.receives
    def some_method_with_event(self, event: Event[SomeModel]):
        return event.data.message


def test_receives_data_validation():
    """Test that the @receives correctly validates the data type of the event."""
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
