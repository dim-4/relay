import pytest
from relay.bindings import Binding, Listener, Emitter, Bindings
from relay.relay import Relay


class DummyRelay(Relay):
    """ Mock Relay class for testing purposes """

    def listener_method(self, event):
        pass

    @classmethod
    def class_listener_method(cls, event):
        pass

def standalone_function(event):
    """ Mock standalone function for testing purposes """
    pass


def test_get_by_relay():
    Bindings.clear()
    relay_instance = DummyRelay()

    # Creating some bindings
    listener_binding = Listener(method=relay_instance.listener_method)
    emitter_binding = Emitter(method=relay_instance.listener_method)

    # Adding bindings
    Bindings.add(listener_binding)
    Bindings.add(listener_binding)
    Bindings.add(emitter_binding)

    # Retrieving by relay instance
    bindings = Bindings.get_by_relay(relay_instance)
    assert len(bindings) == 2
    assert listener_binding in bindings
    assert emitter_binding in bindings

    # Clean up for other tests
    Bindings.remove(listener_binding)
    Bindings.remove(emitter_binding)


def test_get_by_method():
    Bindings.clear()
    relay_instance = DummyRelay()

    # Creating a binding for the instance method
    listener_binding = Listener(method=relay_instance.listener_method)
    class_binding = Listener(method=DummyRelay.class_listener_method)

    # Adding bindings
    Bindings.add(listener_binding)
    Bindings.add(class_binding)

    # Retrieving by method
    instance_bindings = Bindings.get_by_method(relay_instance.listener_method)
    assert len(instance_bindings) == 1
    assert listener_binding in instance_bindings

    class_bindings = Bindings.get_by_method(DummyRelay.class_listener_method)
    assert len(class_bindings) == 1
    assert class_binding in class_bindings

    # Clean up for other tests
    Bindings.remove(listener_binding)
    Bindings.remove(class_binding)


def test_get_by_method_no_bindings():
    Bindings.clear()
    bindings = Bindings.get_by_method(standalone_function)
    assert len(bindings) == 0  # Ensure no bindings for standalone methods

# Testing get_by_event

def test_get_by_event():
    Bindings.clear()
    relay_instance = DummyRelay()

    # Creating some bindings
    listener_binding1 = Listener(method=relay_instance.listener_method, 
                                 channel="channelA", event_type="eventX")
    listener_binding2 = Listener(method=relay_instance.listener_method, 
                                 channel="channelB", event_type="eventX")
    listener_binding3 = Listener(method=relay_instance.listener_method, 
                                 channel="channelA123", event_type="eventY")
    listener_binding4 = Listener(method=relay_instance.listener_method, 
                                 channel="channelCabcXYZ123", 
                                 event_type="eventZ")

    # Adding bindings
    Bindings.add(listener_binding1)
    Bindings.add(listener_binding2)
    Bindings.add(listener_binding3)
    Bindings.add(listener_binding4)

    # Retrieving by specific channel and event type
    bindings = Bindings.get_by_event("channelA", "eventX")
    assert len(bindings) == 1
    assert listener_binding1 in bindings

    # Using wildcard for event type
    all_bindings_channelA = Bindings.get_by_event("channelA*", "*")
    assert len(all_bindings_channelA) == 2
    assert listener_binding1 in all_bindings_channelA
    assert listener_binding3 in all_bindings_channelA

    # Using wildcard for channel
    all_bindings_eventX = Bindings.get_by_event("*", "eventX")
    assert len(all_bindings_eventX) == 2
    assert listener_binding1 in all_bindings_eventX
    assert listener_binding2 in all_bindings_eventX

    # Using partial wildcards for channel and event type
    partial_bindings = Bindings.get_by_event("channelA*", "event*")
    assert len(partial_bindings) == 2
    assert listener_binding1 in partial_bindings
    assert listener_binding3 in partial_bindings

    # Using more complex patterns
    complex_pattern_bindings = Bindings.get_by_event("channelC*XYZ*123", "*")
    assert len(complex_pattern_bindings) == 1
    assert listener_binding4 in complex_pattern_bindings


def test_mixed_patterns():
    Bindings.clear()
    relay_instance = DummyRelay()

    # Set up mock bindings
    listener_binding3 = Listener(method=relay_instance.listener_method, 
                                 channel="channelA123abc", event_type="eventY")
    Bindings.add(listener_binding3)

    mixed_bindings = Bindings.get_by_event("channelA123*", "eventY")
    assert len(mixed_bindings) == 1
    assert listener_binding3 in mixed_bindings

    Bindings.remove(listener_binding3)


def test_nested_wildcards():
    Bindings.clear()
    relay_instance = DummyRelay()

    listener_binding = Listener(method=relay_instance.listener_method,
                                channel="channelAXYZB123", event_type="eventX")
    Bindings.add(listener_binding)

    nested_bindings = Bindings.get_by_event("channelA*B*123", "eventX")
    assert len(nested_bindings) == 1
    assert listener_binding in nested_bindings

    Bindings.remove(listener_binding)


def test_no_matches():
    Bindings.clear()
    no_matches = Bindings.get_by_event("channelZ", "eventZ")
    assert len(no_matches) == 0


def test_only_wildcards():
    Bindings.clear()
    relay_instance = DummyRelay()

    # Set up mock bindings
    listener_binding1 = Listener(method=relay_instance.listener_method, 
                                 channel="channelA", event_type="eventX")
    listener_binding2 = Listener(method=relay_instance.listener_method, 
                                 channel="channelB", event_type="eventX")
    Bindings.add(listener_binding1)
    Bindings.add(listener_binding2)

    all_bindings = Bindings.get_by_event("*", "*")
    assert len(all_bindings) == 2
    assert listener_binding1 in all_bindings
    assert listener_binding2 in all_bindings

    Bindings.remove(listener_binding1)
    Bindings.remove(listener_binding2)


def test_long_patterns():
    Bindings.clear()
    relay_instance = DummyRelay()

    listener_binding = Listener(
        method=relay_instance.listener_method,
        channel="channelALongPatternHereABCAnotherPatternXYZ",
        event_type="eventXLongPatternHere")
    Bindings.add(listener_binding)

    long_bindings = Bindings.get_by_event("channelA*Pattern*XYZ", 
                                          "eventX*PatternHere")
    assert len(long_bindings) == 1
    assert listener_binding in long_bindings

    Bindings.remove(listener_binding)


def test_filter_check():
    Bindings.clear()
    relay_instance = DummyRelay()

    listener_binding = Listener(method=relay_instance.listener_method, 
                                channel="channelA", event_type="eventX")
    emitter_binding = Emitter(method=relay_instance.listener_method, 
                              channel="channelB", event_type="eventX")

    Bindings.add(listener_binding)
    Bindings.add(emitter_binding)

    listener_results = Bindings.get_by_event("channelA", "eventX", filter_=Listener)
    assert len(listener_results) == 1
    assert listener_binding in listener_results

    Bindings.remove(listener_binding)
    Bindings.remove(emitter_binding)


def test_patterns_at_edges():
    Bindings.clear()
    relay_instance = DummyRelay()

    listener_binding1 = Listener(method=relay_instance.listener_method, 
                                 channel="channelA", event_type="eventX")
    Bindings.add(listener_binding1)

    edge_bindings = Bindings.get_by_event("channelA", "*eventX")
    assert len(edge_bindings) == 1
    assert listener_binding1 in edge_bindings

    Bindings.remove(listener_binding1)


def test_special_characters_in_patterns():
    Bindings.clear()
    relay_instance = DummyRelay()

    listener_binding = Listener(method=relay_instance.listener_method, 
                                channel="channel$A^B#C", event_type="event!X@Y")
    Bindings.add(listener_binding)

    special_bindings = Bindings.get_by_event("channel$A^*", "event!X@*")
    assert len(special_bindings) == 1
    assert listener_binding in special_bindings

    Bindings.remove(listener_binding)
