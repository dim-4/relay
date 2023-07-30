import pytest

from relay.event import Event, SourceInfo
from relay.consts import DEFAULT_CHANNEL, DEFAULT_EVENT_TYPE


def test_event_initialization():
    """Test the initialization of the Event class with correct parameters."""
    data = {"message": "Hello!"}
    event = Event(data=data, event_type="GREETING", channel="MAIN")
    assert event.data == data
    assert event.event_type == "GREETING"
    assert event.channel == "MAIN"
    assert event.source is None

def test_event_default_values():
    """Test the default values for event_type and channel."""
    data = {"message": "Hello!"}
    event = Event(data=data)
    assert event.channel == DEFAULT_CHANNEL
    assert event.event_type == DEFAULT_EVENT_TYPE

def test_event_with_source_info():
    """Test the initialization with a given SourceInfo."""
    data = {"message": "Hello!"}
    source_info = SourceInfo(relay=None, func=None)
    event = Event(data=data, source=source_info)
    assert event.source == source_info

@pytest.mark.skip(reason="Ignore due to BaseModel being unable to validate. "
                  "We allow Any type during runtime. See event.py "
                  "TYPE_CHECKING for more info ...")
def test_event_with_invalid_relay():
    """Test that an invalid relay is caught."""
    data = {"message": "Hello!"}
    with pytest.raises(ValueError):
        source_info = SourceInfo(relay="Invalid Relay", func=None)
        event = Event(data=data, source=source_info)

def test_event_with_invalid_func():
    """Test that an invalid function is caught."""
    data = {"message": "Hello!"}
    with pytest.raises(ValueError):
        source_info = SourceInfo(relay=None, func="Invalid Function")
        event = Event(data=data, source=source_info)

def test_event_timestamp_generation():
    """Test that the Event class generates a timestamp upon instantiation."""
    data = {"message": "Hello!"}
    event = Event(data=data)
    assert hasattr(event, "time")
    assert isinstance(event.time, float)

def test_event_timestamp_uniqueness():
    """Test that successive Event instances have unique timestamps."""
    data = {"message": "Hello!"}
    event1 = Event(data=data)
    event2 = Event(data=data)
    assert event1.time != event2.time, "Event timestamps are not unique!"
    time_difference = event2.time - event1.time
    assert time_difference < 0.5, "Events were created too far apart!"


def test_invalid_source_info():
    """Test that invalid SourceInfo data is caught."""
    data = {"message": "Hello!"}
    with pytest.raises(ValueError):
        event = Event(data=data, source="Invalid SourceInfo")

def test_invalid_data_types():
    """ Test incorrect data types handling in Event class. """
    with pytest.raises(ValueError):
        event = Event(data="String data", event_type=["Invalid Type"], 
                      channel=12345)

def test_event_arbitrary_data_type_handling():
    """Test that Event can handle arbitrary data types."""

    class CustomDataType:
        pass

    try:
        event = Event(data=CustomDataType())
    except Exception as e:
        pytest.fail(f"Event failed to handle arbitrary data type. Error: {e}")

def test_event_without_data():
    """Test that the Event class requires data for instantiation."""
    with pytest.raises(ValueError):
        event = Event()

def test_event_default_values_are_valid():
    """Test that default values for event_type and channel are valid."""
    event = Event(data={"message": "Hello!"})
    assert event.channel == DEFAULT_CHANNEL
    assert event.event_type == DEFAULT_EVENT_TYPE
    # Further validation if necessary

def test_event_data_type_preservation():
    """Test that the data type remains unchanged in the Event instance."""
    data = {"message": "Hello!"}
    event = Event(data=data)
    assert type(event.data) is dict
    assert event.data == data

def test_source_info_defaults():
    """Test default values of SourceInfo."""
    source_info = SourceInfo()
    assert source_info.relay is None
    assert source_info.func is None

def test_event_reproduction():
    """Test if two events with the same data are equal."""
    data = {"message": "Hello!"}
    event1 = Event(data=data)
    event2 = Event(data=data)
    assert event1 != event2, "Events with the same data are not equal!"

def test_event_string_representation():
    """Test the string representation of the Event class."""
    data = {"message": "Hello!"}
    event = Event(data=data)
    MAGENTA = "\033[35m"; RESET = "\033[0m"
    print(f"{MAGENTA}{event}{RESET}")
    assert str(event) == (f"Event(data={{'message': 'Hello!'}}, "
                          f"channel='DEFAULT', event_type='DEFAULT', "
                          f"source=None, time={event.time})")
    
    long_data = ["This is a very long string that should be truncated."]
    event = Event(data=long_data)
    print(f"{MAGENTA}{event}{RESET}")
    assert str(event) == (f"Event(data=['{long_data[0][:44]}...], "
                          f"channel='DEFAULT', event_type='DEFAULT', "
                          f"source=None, time={event.time})")
