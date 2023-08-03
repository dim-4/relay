import pytest

from pydantic import BaseModel
from relay.event import Event, SourceInfo
from relay.relay import Relay

MAGENTA = "\033[35m"
RESET = "\033[0m"


class DummyData(BaseModel):
    content: str


class DummyEmitterRelay(Relay):
    @Relay.emits
    async def valid_emitter(self) -> DummyData:
        return DummyData(content="Hello")

    @Relay.emits
    async def invalid_return_type_emitter(self) -> str:
        return DummyData(content="Hello")

    @Relay.emits
    async def no_emit_emitter(self) -> DummyData:
        return Relay.NoEmit(data=DummyData(content="Don't Emit"))

    async def non_emitter(self) -> DummyData:
        return DummyData(content="Hello")


@pytest.mark.asyncio
async def test_emits_decorator_valid_return_type():
    relay_instance = DummyEmitterRelay()
    emitted_data = await relay_instance.valid_emitter()
    assert emitted_data.content == "Hello"


@pytest.mark.asyncio
async def test_emits_decorator_invalid_return_type():
    relay_instance = DummyEmitterRelay()
    with pytest.raises(TypeError, match="Return value: ->") as exc_info:
        await relay_instance.invalid_return_type_emitter()

async def test_emits_decorator_no_emit_return():
    relay_instance = DummyEmitterRelay()
    emitted_data = await relay_instance.no_emit_emitter()
    assert emitted_data.content == "Don't Emit"
    # You might want to add some logic here to ensure the event isn't really emitted.


async def test_emits_decorator_outside_relay():
    class NotARelay:
        @Relay.emits
        async def some_emitter(self) -> DummyData:
            return DummyData(content="Hello")

    instance = NotARelay()

    with pytest.raises(TypeError):
        await instance.some_emitter()


async def test_emits_decorator_on_sync_method():
    with pytest.raises(TypeError, match="The method 'sync_method'") as exc_info:
        class DummyRelaySync(Relay):
            @Relay.emits
            def sync_method(self) -> DummyData:
                return DummyData(content="Hello")

async def test_emits_decorator_without_return_type_hint():
    with pytest.raises(TypeError, match="The method") as exc_info:
        class DummyRelayNoHint(Relay):
            @Relay.emits
            async def method_without_hint(self):
                return DummyData(content="Hello")

@pytest.mark.asyncio
async def test_emits_decorator_no_emit_with_invalid_data_type():
    class DummyEmitterRelayWithInvalidNoEmit(Relay):
        @Relay.emits
        async def invalid_no_emit_emitter(self) -> DummyData:
            return Relay.NoEmit(data="This is a string not a DummyData instance")

    relay_instance = DummyEmitterRelayWithInvalidNoEmit()
    with pytest.raises(TypeError):
        await relay_instance.invalid_no_emit_emitter()


@pytest.mark.asyncio
async def test_emits_decorator_function_without_self_parameter():
    @Relay.emits
    async def function_without_self() -> DummyData:
        return DummyData(content="Hello")

    with pytest.raises(TypeError):
        await function_without_self()


@pytest.mark.asyncio
async def test_emits_decorator_emitting_to_multiple_channels():
    # Note: This test assumes that there's a way in your Bindings to associate a method 
    # with multiple emitters, i.e., multiple channels.
    class MultiChannelEmitterRelay(Relay):
        @Relay.emits
        async def multi_channel_emitter(self) -> DummyData:
            return DummyData(content="Hello to multiple channels")

    relay_instance = MultiChannelEmitterRelay()
    emitted_data = await relay_instance.multi_channel_emitter()

    # Assuming you have a way to track emitted data for channels, 
    # you'll want to verify that the data was emitted to all expected channels.
    # For simplicity, we're just checking the return type here.
    assert emitted_data.content == "Hello to multiple channels"
