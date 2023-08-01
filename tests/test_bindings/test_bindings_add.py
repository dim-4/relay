import pytest
from relay.bindings import Binding, Listener, Emitter, Bindings
from relay.relay import Relay


class DummyRelay(Relay):
    def listener_method(self, *args, **kwargs):
        pass
    
    @classmethod
    def class_listener_method(cls, *args, **kwargs):
        pass


class NonRelayClass:
    @classmethod
    def class_method(cls, *args, **kwargs):
        pass


class CallableObject:
    def __call__(self, *args, **kwargs):
        pass


# Function outside of class
def dummy_function(*args, **kwargs):
    pass

@pytest.fixture
def dummy_relay():
    return DummyRelay()

@pytest.fixture
def listener_binding(dummy_relay:DummyRelay):
    return Listener(method=dummy_relay.listener_method)

@pytest.fixture
def emitter_binding(dummy_relay:DummyRelay):
    return Emitter(method=dummy_relay.listener_method)


def test_add_binding():
    relay = DummyRelay()
    binding = Binding(method=relay.listener_method)
    Bindings.add(binding)
    assert binding in Bindings._by_function[relay.listener_method]

def test_add_binding_from_outside():
    err_msg="Binding method must come from Relay."
    with pytest.raises(ValueError, match=err_msg):
        binding = Binding(method=dummy_function)
        Bindings.add(binding)

def test_add_listener(dummy_relay, listener_binding):
    Bindings.add(listener_binding)
    assert listener_binding in Bindings._by_function[dummy_relay.listener_method]
    assert listener_binding in Bindings._by_relay[dummy_relay]
    
    chnl_type_dict = Bindings._by_chnl_and_type[listener_binding.channel]
    assert listener_binding in chnl_type_dict[listener_binding.event_type]

def test_add_emitter(dummy_relay, emitter_binding):
    Bindings.add(emitter_binding)
    assert emitter_binding in Bindings._by_function[dummy_relay.listener_method]
    assert emitter_binding in Bindings._by_relay[dummy_relay]
    
    chnl_type_dict = Bindings._by_chnl_and_type[emitter_binding.channel]
    assert emitter_binding in chnl_type_dict[emitter_binding.event_type]

def test_add_classmethod():
    binding = Binding(method=DummyRelay.class_listener_method)
    Bindings.add(binding)
    assert binding in Bindings._by_function[DummyRelay.class_listener_method]
    # instance becomes the class itself for classmethods
    assert binding in Bindings._by_relay[DummyRelay]  
    
    chnl_type_dict = Bindings._by_chnl_and_type[binding.channel]
    assert binding in chnl_type_dict[binding.event_type]

def test_add_invalid_method_raises_exception():
    err_msg="Binding method must come from Relay."
    with pytest.raises(ValueError, match=err_msg):
        binding = Binding(method=print)
        Bindings.add(binding)

def test_multiple_bindings_same_function(dummy_relay: DummyRelay):
    binding1 = Binding(method=dummy_relay.listener_method)
    binding2 = Binding(method=dummy_relay.listener_method)
    
    Bindings.add(binding1)
    Bindings.add(binding2)

    # Check if both bindings are in the appropriate dictionaries
    assert binding1 in Bindings._by_function[dummy_relay.listener_method]
    assert binding2 in Bindings._by_function[dummy_relay.listener_method]

@pytest.mark.skip(reason="Bindings can't check if method belongs to Relay")
def test_add_classmethod_from_non_relay_class():
    err_msg = "Binding method must come from Relay."
    with pytest.raises(ValueError, match=err_msg):
        binding = Binding(method=NonRelayClass.class_method)
        Bindings.add(binding)

def test_add_callable_object_raises_exception():
    callable_obj = CallableObject()
    err_msg = "Binding method must come from Relay."
    
    with pytest.raises(ValueError, match=err_msg):
        binding = Binding(method=callable_obj)
        Bindings.add(binding)


@pytest.mark.parametrize("channel,event_type", [
    ("channel_1", "event_1"),
    ("channel_2", "event_2"),
])
def test_bindings_different_channels_and_event_types(channel, event_type, 
                                                     dummy_relay: DummyRelay):
    binding = Binding(method=dummy_relay.listener_method, channel=channel, 
                      event_type=event_type)
    Bindings.add(binding)
    
    # Ensure that the binding is stored correctly based on channel and event type
    assert binding in Bindings._by_chnl_and_type[channel][event_type]
