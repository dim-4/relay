import pytest

import asyncio
import logging
import time
from pydantic import BaseModel
from typing import Any
from relay.event import Event, SourceInfo
from relay.relay import Relay
from relay.bindings import Listener, Emitter, Bindings

logging.basicConfig(level=logging.DEBUG,
                    format=('[%(levelname)s] [%(asctime)s] '
                            '[%(module)s:%(lineno)d] %(message)s'),
                    datefmt='%Y-%m-%d %H-%M-%S')
logger = logging.getLogger(__name__)
GREEN, RST = "\033[92m", "\033[0m"


class DummyData(BaseModel):
    content: str

# Simple emitter call and receiver callback check 

class DummyRelayMessagingSimple(Relay):
    def __init__(self) -> None:
        super().__init__()
        self.emitter_called = False
        self.listener_called = asyncio.Event()

    @Relay.listens
    async def listener(self, event:Event[DummyData]):
        data = "listener_1: " + event.data.content
        self.listener_response = data
        # logger.info(f"{GREEN}listener called ! <{data}>{RST}")
        self.listener_called.set()

    @Relay.emits
    async def emitter(self) -> DummyData:
        # logger.info(f"{GREEN}emitter called !{RST}")
        self.emitter_called = True
        return DummyData(content="emitter_1")

async def test_messaging_simple():
    Bindings.clear()

    relay = DummyRelayMessagingSimple()

    # Create a channel and event type for communication
    channel = "test_channel"
    event_type = "test_event"


    # Setting up the binding between emitter and listener
    emitter_binding = Emitter(method=relay.emitter, 
                              channel=channel, 
                              event_type=event_type)
    listener_binding = Listener(method=relay.listener, 
                                channel=channel, 
                                event_type=event_type)
    
    Bindings.add(emitter_binding)
    Bindings.add(listener_binding)

    # Trigger the emitter
    await relay.emitter()

    # Wait until the listener has been called
    await relay.listener_called.wait()

    # Assert that the emitter was indeed called
    assert relay.emitter_called, "Emitter was not called"

    # Check if listener has processed the emitted event
    expected_response = "listener_1: emitter_1"
    assert relay.listener_response == expected_response, \
           f"Expected '{expected_response}' but got '{relay.listener_response}'"


# Emitter call with invalid type

class DummyRelayInvalidType(Relay):
    def __init__(self) -> None:
        super().__init__()
        self.emitter_called = False
    
    @Relay.emits
    async def emitter(self) -> DummyData:
        # logger.info(f"{GREEN}emitter called !{RST}")
        self.emitter_called = True
        # Here we are returning an integer even though DummyData is expected
        return 123

async def test_invalid_type_emission():
    Bindings.clear()

    relay = DummyRelayInvalidType()

    # Create a channel and event type for communication
    channel = "test_channel"
    event_type = "test_event"

    # Setting up the binding for emitter
    emitter_binding = Emitter(method=relay.emitter, 
                              channel=channel, 
                              event_type=event_type)
    Bindings.add(emitter_binding)

    # Trigger the emitter and expect a TypeError because the return type is wrong
    with pytest.raises(TypeError):
        await relay.emitter()


# Emitter call without any listeners, making sure no errors raised

class DummyRelayNoListener(Relay):
    def __init__(self) -> None:
        super().__init__()
        self.emitter_called = False
    @Relay.emits
    async def emitter(self) -> DummyData:
        # logger.info(f"{GREEN}emitter called !{RST}")
        self.emitter_called = True
        return DummyData(content="emitter_no_listener")

async def test_emission_without_listeners():
    Bindings.clear()

    relay = DummyRelayNoListener()

    # Create a channel and event type for communication
    channel = "test_channel"
    event_type = "test_event"

    # Setting up the binding for emitter
    emitter_binding = Emitter(method=relay.emitter, 
                              channel=channel, 
                              event_type=event_type)
    Bindings.add(emitter_binding)

    # Trigger the emitter
    await relay.emitter()

    # Assert that the emitter was indeed called
    assert relay.emitter_called, "Emitter was not called in the absence of any listener"


# Emitter call with multiple listeners

class DummyRelayMultiListener(Relay):
    def __init__(self) -> None:
        super().__init__()
        self.l1_called = asyncio.Event()
        self.l2_called = asyncio.Event()

    @Relay.listens
    async def listener1(self, event:Event[DummyData]):
        # logger.info(f"{GREEN}listener1 called ! <{event.data.content}>{RST}")
        self.l1_called.set()

    @Relay.listens
    async def listener2(self, event:Event[DummyData]):
        # logger.info(f"{GREEN}listener2 called ! <{event.data.content}>{RST}")
        self.l2_called.set()

    @Relay.emits
    async def emitter(self) -> DummyData:
        return DummyData(content="emitter")

async def test_multiple_listeners():
    Bindings.clear()

    relay = DummyRelayMultiListener()

    # Create a channel and event type for communication
    channel = "test_channel"
    event_type = "test_event"

    # Setting up the bindings for emitter and listeners
    emitter_binding = Emitter(method=relay.emitter, 
                              channel=channel, 
                              event_type=event_type)
    listener1_binding = Listener(method=relay.listener1, 
                                 channel=channel, 
                                 event_type=event_type)
    listener2_binding = Listener(method=relay.listener2, 
                                 channel=channel, 
                                 event_type=event_type)

    # Add bindings
    Bindings.add(emitter_binding)
    Bindings.add(listener1_binding)
    Bindings.add(listener2_binding)
    
    # Trigger the emitter
    await relay.emitter()

    # Wait until the listeners are called
    await relay.l1_called.wait()
    await relay.l2_called.wait()

    assert relay.l1_called.is_set()
    assert relay.l2_called.is_set()


# Multiple events emitted in quick succession, checking order

class DummyRelayEventOrder(Relay):
    def __init__(self) -> None:
        super().__init__()
        self.results = []

    @Relay.emits
    async def emitter(self, content: str) -> DummyData:
        # Return the content along with a timestamp
        return DummyData(content=content + "_" + str(time.time()))

    @Relay.listens
    async def listener(self, event: Event[DummyData]):
        # Record executions
        self.results.append(event.data.content)

async def test_event_order():
    Bindings.clear()

    relay = DummyRelayEventOrder()

    # Create a channel and event type for communication
    channel = "test_channel"
    event_type = "test_event"

    # Setting up the bindings for emitter and listener
    emitter_binding = Emitter(method=relay.emitter, 
                              channel=channel, 
                              event_type=event_type)
    listener_binding = Listener(method=relay.listener, 
                                channel=channel, 
                                event_type=event_type)
    
    Bindings.add(emitter_binding)
    Bindings.add(listener_binding)

    # Trigger the emitter with series of events
    for i in range(5):
        await relay.emitter(f"event_{i}")

    await asyncio.sleep(0.01)  # Allow event handling to complete

    # Check event processing order
    results = relay.results
    for i in range(len(results) - 1):
        _, timestamp1 = results[i].rsplit("_", 1)
        _, timestamp2 = results[i + 1].rsplit("_", 1)
        assert timestamp1 < timestamp2


# Test events when listeners have expected sources specified

class DummyRelayEventFromSource(Relay):
    def __init__(self) -> None:
        super().__init__()
        self.other_results = []
        self.own_results = []

    @Relay.listens
    async def listener(self, event: Event[DummyData]):
        # Record executions
        self.other_results.append(event.data.content)
    
    @Relay.listens
    async def own_listener(self, event: Event[DummyData]):
        # Record executions
        self.own_results.append(event.data.content)

    @Relay.emits
    async def emitter(self, content: str) -> DummyData:
        return DummyData(content=content)

        
class OtherRelay(Relay):
    @Relay.emits
    async def other_emitter(self, content: str) -> DummyData:
        return DummyData(content=content)


async def test_event_from_specific_source():
    Bindings.clear()

    relay = DummyRelayEventFromSource()
    other_relay = OtherRelay()

    # Create a channel and event type for communication
    channel = "test_channel"
    event_type = "test_event"

    # Setting up the bindings for emitter and listener
    other_emitter_binding = Emitter(method=other_relay.other_emitter, 
                                    channel=channel, 
                                    event_type=event_type)

    listener_binding = Listener(method=relay.listener, 
                                channel=channel, 
                                event_type=event_type, 
                                # emitter is not relay, it's other_relay so this shouldn't go through
                                source=SourceInfo(relay=relay, 
                                                  emitter=other_relay.other_emitter))

    emitter_binding = Emitter(method=relay.emitter,
                              channel=channel,
                              event_type=event_type)
    own_listener_binding = Listener(method=relay.own_listener,
                                    channel=channel,
                                    event_type=event_type,
                                    # this should go through because emitter is relay
                                    source=SourceInfo(relay=relay,
                                                      emitter=relay.emitter))
    
    # in these bindings, listener is not expecting source of other_emitter_binding
    Bindings.add(other_emitter_binding)
    Bindings.add(listener_binding)

    # in these bindings, listener is expecting source of emitter_binding
    Bindings.add(emitter_binding)
    Bindings.add(own_listener_binding)

    
    # Trigger the emitter
    await other_relay.other_emitter("this event should not be received by the listener")
    await relay.emitter("this event should be received by the listener")

    await asyncio.sleep(0.01)  # Allow event handling to complete
    
    # Check that the listener did not receive the event
    assert len(relay.other_results) == 0

    # Check that the listener received the event
    assert len(relay.own_results) == 1


# test that if exception is raised in listener or emitter, it does not 
# affect other listeners or emitters

class DummyRelayExceptionHandling(Relay):
    def __init__(self) -> None:
        super().__init__()
        self.successful_listener_called = asyncio.Event()

    @Relay.emits
    async def faulty_emitter(self) -> DummyData:
        raise Exception("This is a faulty emitter")

    @Relay.emits
    async def successful_emitter(self) -> DummyData:
        return DummyData(content="emitter")

    @Relay.listens
    async def successful_listener(self, event: Event[DummyData]):
        self.successful_listener_called.set()

    @Relay.listens
    async def faulty_listener(self, event: Event[DummyData]):
        raise Exception("This is a faulty listener (testing purpose)")


async def test_exception_handling():
    Bindings.clear()

    relay = DummyRelayExceptionHandling()

    # Create a channel and event type for communication
    channel = "test_channel"
    event_type = "test_event"

    # Setting up the bindings for emitters and listeners
    successful_emitter_binding = Emitter(method=relay.successful_emitter, 
                                         channel=channel, 
                                         event_type=event_type)
    faulty_emitter_binding = Emitter(method=relay.faulty_emitter, 
                                     channel=channel, 
                                     event_type=event_type)
    successful_listener_binding = Listener(method=relay.successful_listener, 
                                           channel=channel, 
                                           event_type=event_type)
    faulty_listener_binding = Listener(method=relay.faulty_listener, 
                                       channel=channel, 
                                       event_type=event_type)
    
    # Relay.add_binding is the same as Bindings.add
    Relay.add_binding(successful_emitter_binding)
    Relay.add_binding(faulty_emitter_binding)
    Relay.add_binding(successful_listener_binding)
    Relay.add_binding(faulty_listener_binding)

    # Trigger the emitter
    with pytest.raises(Exception, match="This is a faulty emitter"):
        await relay.faulty_emitter()

    assert not relay.successful_listener_called.is_set()

    await relay.successful_emitter()

    # Wait until the successful_listener has been called
    await relay.successful_listener_called.wait()

    # Check that the successful_listener has been called
    assert relay.successful_listener_called.is_set()

    logger.info(f"{GREEN}The exception here was expected. Relax.{RST}")


# testing functionality of adding and removing bindings

class DummyRelayBinding(Relay):
    def __init__(self) -> None:
        super().__init__()
        self.listener_called = asyncio.Event()

    @Relay.listens
    async def listener(self, event:Event[DummyData]):
        self.listener_called.set()

    @Relay.emits
    async def emitter(self) -> DummyData:
        return DummyData(content="emitter")

async def test_add_remove_binding():
    Bindings.clear()
    relay = DummyRelayBinding()

    # Create a channel and event type for communication
    channel = "test_channel"
    event_type = "test_event"

    # Setting up the bindings for emitter and listener
    emitter_binding = Emitter(method=relay.emitter, channel=channel, event_type=event_type)
    listener_binding = Listener(method=relay.listener, channel=channel, event_type=event_type)

    # Adding the bindings
    Relay.add_binding(emitter_binding)
    Relay.add_binding(listener_binding)
    
    # Verifying that the bindings have been added
    assert Bindings.get_by_method(relay.emitter) == [emitter_binding]
    assert Bindings.get_by_method(relay.listener) == [listener_binding]

    # Trigger the emitter
    await relay.emitter()

    # Wait until the listener has been called
    await relay.listener_called.wait()
    relay.listener_called.clear()

    # Test for removing one of the bindings
    Relay.remove_binding(listener_binding)

    # Verifying that the listener binding has been removed
    assert Bindings.get_by_method(relay.listener) == []

    # Trigger the emitter - this time the listener shouldn't be called
    await relay.emitter()

    await asyncio.sleep(0.01)  # just in case, allow event handling to complete

    # Check that the listener has not been called
    assert not relay.listener_called.is_set()


# test that NoEmit does not emit anything, but returns data

class DummyRelayNoEmit(Relay):
    def __init__(self) -> None:
        super().__init__()
        self.listener_called = asyncio.Event()

    @Relay.listens
    async def listener(self, event:Event[DummyData]):
        self.listener_called.set()

    @Relay.emits
    async def emitter(self) -> DummyData:
        return Relay.NoEmit(data=DummyData(content="emitter"))

async def test_no_emit():
    Bindings.clear()

    relay = DummyRelayNoEmit()

    # Create a channel and event type for communication
    channel = "test_channel"
    event_type = "test_event"

    # Setting up the bindings for emitter and listener
    emitter_binding = Emitter(method=relay.emitter, 
                              channel=channel, 
                              event_type=event_type)
    listener_binding = Listener(method=relay.listener, 
                                channel=channel, 
                                event_type=event_type)

    # Adding the bindings
    Relay.add_binding(emitter_binding)
    Relay.add_binding(listener_binding)
    
    # Trigger the emitter
    returned_data = await relay.emitter()

    # make sure data is still returned
    assert returned_data.content == "emitter"

    # give some sleep time for possible listener execution
    await asyncio.sleep(0.01)

    # Check that the listener has NOT been called
    assert not relay.listener_called.is_set()


# Chain example with a method having both emitter and listener decorators
"""
@Relay.emits
@Relay.listens
async def emitter_listener(self, ...) ...

@Relay.listens
async def listener(self, ...) ...

@Relay.emits
async def emitter(self, ...) ...

We make emitter emit something that is listened by emitter_listener. 
This emitter_listener, once it receives this will emit the data which 
will be listened by listener
"""

class DummyRelayChain(Relay):
    def __init__(self) -> None:
        super().__init__()
        self.final_listener_called = asyncio.Event()

    @Relay.listens
    async def final_listener(self, event:Event[DummyData]):
        self.final_data = event.data.content
        self.final_listener_called.set()

    @Relay.emits
    @Relay.listens
    async def emitter_listener(self, event:Event[DummyData]) -> DummyData:
        # re-emit the data with some modification
        return DummyData(content=f"emitter_listener: {event.data.content}")

    @Relay.emits
    async def starter_emitter(self) -> DummyData:
        return DummyData(content="starter_emitter")


async def test_emitter_listener():
    Bindings.clear()

    relay = DummyRelayChain()

    # Create a channel and event type for communication
    channel = "test_channel"
    event_type = "test_event"

    # Setting up the bindings for the starter_emitter, emitter_listener and final_listener
    starter_emitter_binding = Emitter(method=relay.starter_emitter, 
                                      channel=channel, event_type=event_type)
    emitter_listener_binding = Emitter(method=relay.emitter_listener, 
                                       channel=channel, event_type=event_type)
    emitter_listener_listener_binding = Listener(method=relay.emitter_listener, 
                                                 channel=channel, event_type=event_type)
    final_listener_binding = Listener(method=relay.final_listener, 
                                      channel=channel, event_type=event_type)

    # Adding the bindings
    Relay.add_binding(starter_emitter_binding)
    Relay.add_binding(emitter_listener_binding)
    Relay.add_binding(emitter_listener_listener_binding)
    Relay.add_binding(final_listener_binding)

    # Trigger the starter_emitter
    await relay.starter_emitter()

    # Wait until the final_listener has been called
    await relay.final_listener_called.wait()
    
    # Assert that the final_data in final_listener matches what is expected
    assert relay.final_data == "emitter_listener: starter_emitter", \
        f"Expected 'emitter_listener: starter_emitter' but got '{relay.final_data}'"