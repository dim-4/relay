import pytest

import asyncio
import logging
from pydantic import BaseModel
from typing import Any
from relay.event import Event, SourceInfo
from relay.relay import Relay
from relay.bindings import Listener, Emitter, Bindings

logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s] [%(asctime)s] %(message)s',
                    datefmt='%Y-%m-%d %H-%M-%S')
logger = logging.getLogger(__name__)
GREEN, RST = "\033[92m", "\033[0m"


class DummyData(BaseModel):
    content: str

# Complex tests for Relay emission

class DummyRelayMessagingSimple(Relay):

    def __init__(self) -> None:
        super().__init__()
        self.emitter_called = False
        self.listener_response = None


    @Relay.listens
    async def listener(self, event:Event[DummyData]):
        data = "listener_1: " + event.data.content
        self.listener_response = data
        logger.info(f"{GREEN}listener called ! <{data}>{RST}")
    
    @Relay.emits
    async def emitter(self) -> DummyData:
        logger.info(f"{GREEN}emitter called !{RST}")
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

    await asyncio.sleep(0.001)

    # Assert that the emitter was indeed called
    assert relay.emitter_called, "Emitter was not called"

    # Check if listener has processed the emitted event
    expected_response = "listener_1: emitter_1"
    assert relay.listener_response == expected_response, \
           f"Expected '{expected_response}' but got '{relay.listener_response}'"
