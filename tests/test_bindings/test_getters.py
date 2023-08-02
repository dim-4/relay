import pytest
from relay.bindings import Binding, Listener, Emitter, Bindings
from relay.relay import Relay


class DummyRelay:
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


# TODO: think about these things before. Especially, the WILDCARD parts
# THINK ABOUT PARTIAL EVENTS TOO: event_type = "some*"

# def test_get_by_event():
#     Bindings.clear()
#     relay_instance = DummyRelay()

#     # Creating some bindings
#     listener_binding = Listener(method=relay_instance.listener_method, 
#                                 channel="channelA", event_type="eventX")
#     emitter_binding = Emitter(method=relay_instance.listener_method, 
#                               channel="channelA", event_type="eventY")

#     # Adding bindings
#     Bindings.add(listener_binding)
#     Bindings.add(emitter_binding)

#     # Retrieving by channel and event type
#     bindings = Bindings.get_by_event("channelA", "eventX")
#     assert len(bindings) == 1
#     assert listener_binding in bindings

#     all_bindings = Bindings.get_by_event("channelA", "*")
#     assert len(all_bindings) == 2
#     assert listener_binding in all_bindings
#     assert emitter_binding in all_bindings

#     # Clean up for other tests
#     Bindings.remove(listener_binding)
#     Bindings.remove(emitter_binding)
