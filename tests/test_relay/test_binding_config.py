import pytest

import asyncio
import logging
import time
from pydantic import BaseModel
from typing import Any
from relay.event import Event, SourceInfo
from relay.relay import Relay
from relay.bindings import Listener, Emitter, Binding, Bindings

logging.basicConfig(level=logging.DEBUG,
                    format=('[%(levelname)s] [%(asctime)s] '
                            '[%(module)s:%(lineno)d] %(message)s'),
                    datefmt='%Y-%m-%d %H-%M-%S')
logger = logging.getLogger(__name__)
GREEN, RST = "\033[92m", "\033[0m"


class DummyData(BaseModel):
    content: str


class DummyRelayWithBindingConfig(Relay):
    def __init__(self, binding_config:list[Binding]=None):
        super().__init__(binding_config)
        self.listener_called = asyncio.Event()

    @Relay.listens
    async def listener(self, event:Event[DummyData]):
        self.listener_called.set()

    @Relay.emits
    async def emitter(self) -> DummyData:
        return DummyData(content="emitter")
        

async def test_with_binding_config():
    Bindings.clear()

    # Create a channel and event type for communication
    channel = "test_channel"
    event_type = "test_event"

    # Setting up the bindings for emitter and listener without binding to an instance
    emitter_binding = Emitter(method=DummyRelayWithBindingConfig.emitter, 
                              channel=channel, 
                              event_type=event_type)
    listener_binding = Listener(method=DummyRelayWithBindingConfig.listener, 
                                channel=channel, 
                                event_type=event_type)

    # Create the Relay instance with the configuration
    relay = DummyRelayWithBindingConfig(binding_config=[emitter_binding, listener_binding])

    # Trigger the emitter (should be bound to the relay instance internally)
    await relay.emitter()

    # Wait until the listener has been called
    await relay.listener_called.wait()

    # Check that the listener (which should be bound to the relay instance internally) was indeed called
    assert relay.listener_called.is_set()
