import pytest
from relay.bindings import Binding, Listener, Emitter, Bindings
from relay.relay import Relay


class DummyRelay(Relay):
    async def listener_method(self, *args, **kwargs):
        pass
    
    @classmethod
    async def class_listener_method(cls, *args, **kwargs):
        pass

    async def another_listener(self, *args, **kwargs):
        pass


@pytest.fixture
def dummy_relay():
    return DummyRelay()


@pytest.fixture
def binding(dummy_relay:DummyRelay):
    return Binding(method=dummy_relay.listener_method)


def test_bindings_clear():
    """
    Ensure the `clear` method resets all Bindings collections.
    """
    dummy_relay = DummyRelay()
    
    binding1 = Binding(method=dummy_relay.listener_method, channel="custom_channel")
    binding2 = Binding(method=dummy_relay.another_listener, channel="custom_channel")
    Bindings.add(binding1)
    Bindings.add(binding2)
    
    assert Bindings._by_chnl_and_type
    assert Bindings._by_relay
    assert Bindings._by_method
    
    Bindings.clear()
    
    assert not Bindings._by_chnl_and_type
    assert not Bindings._by_relay
    assert not Bindings._by_method


def test_remove_binding(binding, dummy_relay):
    Bindings.clear()
    Bindings.add(binding)
    Bindings.remove(binding)
    assert binding not in Bindings._by_method[dummy_relay.listener_method]
    assert binding not in Bindings._by_relay[dummy_relay]
    assert binding not in Bindings._by_chnl_and_type[binding.channel][binding.event_type]


def test_remove_binding_with_relay(dummy_relay):
    Bindings.clear()
    binding = Binding(method=dummy_relay.listener_method)
    Bindings.add(binding)
    Bindings.remove_relay(dummy_relay)
    assert dummy_relay not in Bindings._by_relay
    assert binding not in Bindings._by_method[dummy_relay.listener_method]
    assert binding not in Bindings._by_chnl_and_type[binding.channel][binding.event_type]


def test_remove_classmethod_binding():
    Bindings.clear()
    binding = Binding(method=DummyRelay.class_listener_method)
    Bindings.add(binding)
    Bindings.remove(binding)
    assert binding not in Bindings._by_method[DummyRelay.class_listener_method]
    # for classmethods, the 'instance' is the class itself
    assert binding not in Bindings._by_relay[DummyRelay]
    assert binding not in Bindings._by_chnl_and_type[binding.channel][binding.event_type]

def test_remove_from_empty_binding_collection(binding):
    Bindings.clear()
    try:
        Bindings.remove(binding)
        Bindings.remove(binding)
        Bindings.remove(binding)
        assert True  # If we reached this point, no exception was thrown
    except Exception:
        assert False  # If an exception was thrown, fail the test

def test_remove_nonexistent_binding(binding, dummy_relay):
    Bindings.clear()
    Bindings.remove(binding)  # this should not raise an error even though the binding was not added
    assert binding not in Bindings._by_method[dummy_relay.listener_method]
    assert binding not in Bindings._by_relay[dummy_relay]
    assert binding not in Bindings._by_chnl_and_type[binding.channel][binding.event_type]

def test_remove_none_binding():
    Bindings.clear()
    try:
        Bindings.remove(None)
        assert True  # If we reached this point, no exception was thrown
    except Exception:
        assert False  # If an exception was thrown, fail the test

def test_remove_binding_different_channels(dummy_relay):
    Bindings.clear()
    binding1 = Binding(method=dummy_relay.listener_method, channel="channel1")
    binding2 = Binding(method=dummy_relay.listener_method, channel="channel2")
    Bindings.add(binding1)
    Bindings.add(binding2)
    Bindings.remove(binding1)
    
    assert binding1 not in Bindings._by_chnl_and_type["channel1"][binding1.event_type]
    assert binding2 in Bindings._by_chnl_and_type["channel2"][binding2.event_type]

def test_binding_count_after_adds_and_removes(dummy_relay):
    Bindings.clear()
    binding = Binding(method=dummy_relay.listener_method)
    Bindings.add(binding)
    Bindings.add(binding)  # add it again
    Bindings.remove(binding)

    # Depending on your desired behavior, the binding might still exist or not. Adjust the test accordingly.
    assert binding not in Bindings._by_method[dummy_relay.listener_method]

def test_remove_unbound_relay(dummy_relay):
    Bindings.clear()
    Bindings.remove_relay(dummy_relay)  # this should not raise an error
    assert dummy_relay not in Bindings._by_relay

def test_remove_event_type_after_removing_binding(dummy_relay):
    Bindings.clear()
    binding = Binding(method=dummy_relay.listener_method, event_type="custom_event")
    Bindings.add(binding)
    Bindings.remove(binding)
    assert "custom_event" not in Bindings._by_chnl_and_type[binding.channel]

def test_remove_function_after_removing_all_bindings(dummy_relay):
    Bindings.clear()
    binding1 = Binding(method=dummy_relay.listener_method)
    binding2 = Binding(method=dummy_relay.listener_method, channel="channel2")
    Bindings.add(binding1)
    Bindings.add(binding2)
    Bindings.remove(binding1)
    Bindings.remove(binding2)
    assert dummy_relay.listener_method not in Bindings._by_method

def test_add_remove_multiple_bindings_same_function_different_channels(dummy_relay):
    Bindings.clear()
    binding1 = Binding(method=dummy_relay.listener_method, channel="channel1")
    binding2 = Binding(method=dummy_relay.listener_method, channel="channel2")
    Bindings.add(binding1)
    Bindings.add(binding2)
    Bindings.remove(binding1)
    assert binding1 not in Bindings._by_chnl_and_type["channel1"][binding1.event_type]
    assert binding2 in Bindings._by_chnl_and_type["channel2"][binding2.event_type]
    Bindings.remove(binding2)
    assert binding2 not in Bindings._by_chnl_and_type["channel2"][binding2.event_type]

def test_add_remove_multiple_bindings_different_functions(dummy_relay):
    Bindings.clear()

    binding1 = Binding(method=dummy_relay.listener_method)
    binding2 = Binding(method=dummy_relay.another_listener)
    Bindings.add(binding1)
    Bindings.add(binding2)
    Bindings.remove(binding1)
    assert binding1 not in Bindings._by_method[dummy_relay.listener_method]
    assert binding2 in Bindings._by_method[dummy_relay.another_listener]

def test_remove_relay_multiple_times(dummy_relay):
    Bindings.clear()
    binding = Binding(method=dummy_relay.listener_method)
    Bindings.add(binding)
    Bindings.remove_relay(dummy_relay)
    Bindings.remove_relay(dummy_relay)  # should not raise an error
    assert dummy_relay not in Bindings._by_relay

def test_remove_unbound_function_binding():
    Bindings.clear()
    async def standalone_function(*args, **kwargs):
        pass

    binding = Binding(method=standalone_function)
    # expecting a value error as the function is not bound to Relay
    with pytest.raises(ValueError):  
        Bindings.remove(binding)

def test_interleaved_add_remove_operations(dummy_relay):
    Bindings.clear()
    binding1 = Binding(method=dummy_relay.listener_method, channel="channel1")
    binding2 = Binding(method=dummy_relay.listener_method, channel="channel2")
    binding3 = Binding(method=dummy_relay.listener_method, channel="channel3")
    binding4 = Binding(method=dummy_relay.listener_method, channel="channel4")
    binding5 = Binding(method=dummy_relay.listener_method, channel="channel5")
    
    Bindings.add(binding1)
    Bindings.add(binding2)
    Bindings.add(binding3)
    Bindings.remove(binding2)
    Bindings.add(binding4)
    Bindings.add(binding5)
    Bindings.remove(binding4)

    assert binding1 in Bindings._by_chnl_and_type["channel1"][binding1.event_type]
    assert binding2 not in Bindings._by_chnl_and_type["channel2"][binding2.event_type]
    assert binding3 in Bindings._by_chnl_and_type["channel3"][binding3.event_type]
    assert binding4 not in Bindings._by_chnl_and_type["channel4"][binding4.event_type]
    assert binding5 in Bindings._by_chnl_and_type["channel5"][binding5.event_type]

def test_remove_multiple_event_types(dummy_relay):
    Bindings.clear()
    binding1 = Binding(method=dummy_relay.listener_method, event_type="custom_event1")
    binding2 = Binding(method=dummy_relay.listener_method, event_type="custom_event2")
    Bindings.add(binding1)
    Bindings.add(binding2)
    Bindings.remove(binding1)
    assert "custom_event1" not in Bindings._by_chnl_and_type[binding1.channel]
    assert "custom_event2" in Bindings._by_chnl_and_type[binding2.channel]

def test_add_remove_same_event_type_different_bindings(dummy_relay):
    Bindings.clear()
    binding1 = Binding(method=dummy_relay.listener_method, event_type="custom_event")
    binding2 = Binding(method=dummy_relay.another_listener, event_type="custom_event")
    Bindings.add(binding1)
    Bindings.add(binding2)
    Bindings.remove(binding1)
    assert binding1 not in Bindings._by_method[dummy_relay.listener_method]
    assert binding2 in Bindings._by_method[dummy_relay.another_listener]

def test_remove_binding_added_multiple_times(dummy_relay):
    Bindings.clear()
    binding = Binding(method=dummy_relay.listener_method)
    Bindings.add(binding)
    Bindings.add(binding)  # add again
    Bindings.remove(binding)
    Bindings.remove(binding)  # remove again, shouldn't raise an error
    assert binding not in Bindings._by_method[dummy_relay.listener_method]

def test_remove_channel_after_removing_all_bindings(dummy_relay):
    Bindings.clear()
    binding1 = Binding(method=dummy_relay.listener_method, channel="custom_channel")
    binding2 = Binding(method=dummy_relay.another_listener, channel="custom_channel")
    Bindings.add(binding1)
    Bindings.add(binding2)
    Bindings.remove(binding1)
    Bindings.remove(binding2)
    assert "custom_channel" not in Bindings._by_chnl_and_type

def test_remove_channel_after_all_bindings_removed(dummy_relay):
    """
    Ensure that when all bindings of a channel are removed, 
    the channel itself is removed from `_by_chnl_and_type`.
    """
    Bindings.clear()
    binding1 = Binding(method=dummy_relay.listener_method, channel="custom_channel")
    binding2 = Binding(method=dummy_relay.another_listener, channel="custom_channel")
    Bindings.add(binding1)
    Bindings.add(binding2)
    Bindings.remove(binding1)
    Bindings.remove(binding2)
    assert "custom_channel" not in Bindings._by_chnl_and_type

def test_remove_function_after_all_bindings_removed(dummy_relay):
    """
    Ensure that when all bindings of a specific function are removed, 
    the function key itself is removed from `_by_function`.
    """
    Bindings.clear()
    binding1 = Binding(method=dummy_relay.listener_method)
    binding2 = Binding(method=dummy_relay.listener_method, channel="custom_channel")
    Bindings.add(binding1)
    Bindings.add(binding2)
    Bindings.remove(binding1)
    Bindings.remove(binding2)
    assert dummy_relay.listener_method not in Bindings._by_method

def test_remove_relay_after_all_bindings_removed(dummy_relay):
    """
    Ensure that when all bindings of a specific relay instance are removed, 
    the relay key itself is removed from `_by_relay`.
    """
    Bindings.clear()
    binding1 = Binding(method=dummy_relay.listener_method)
    binding2 = Binding(method=dummy_relay.another_listener, channel="custom_channel")
    Bindings.add(binding1)
    Bindings.add(binding2)
    Bindings.remove(binding1)
    Bindings.remove(binding2)
    assert dummy_relay not in Bindings._by_relay

def test_remove_channel_after_removing_all_event_types(dummy_relay):
    """
    Ensure that when all event types of a specific channel are removed,
    the channel key itself is removed from `_by_chnl_and_type`.
    """
    Bindings.clear()
    binding1 = Binding(method=dummy_relay.listener_method, channel="custom_channel", event_type="event1")
    binding2 = Binding(method=dummy_relay.another_listener, channel="custom_channel", event_type="event2")
    Bindings.add(binding1)
    Bindings.add(binding2)
    Bindings.remove(binding1)
    Bindings.remove(binding2)
    assert "custom_channel" not in Bindings._by_chnl_and_type
