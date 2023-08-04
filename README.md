# Relay

Relay is a Python package that allows asynchronus inter-method communication between classes inheriting from `Relay` class, enabling one method to trigger an event or multiple events with same payload that multiple methods can listen to and respond to. Using Relay, you can create complex event emitting and listening configurations without needing to manually bind each method and handle communication logic. This is achieved through the concept of bindings that define the relationship between an event emitter method and a listening method. 

## Installation

You can install Relay through pip by running:

```
pip install relaypy-async
```

## Features

- **Not just event listeners and emitters**: Relay validates the data emitted with the type hints you provide, and avoids wrong data type errors.
- **Automate event handling**: Pass the binding configuration once during the class instantiation and Relay will automatically call the right methods when a particular event is emitted.
- **Flexible and Extendable**: Relay supports multiple listeners per emitter and multiple emitters per listener.
- **Async**: The methods `Relay` supports must be async and bounded to a class that extends `Relay`.

## How to use

Here is a basic example of using Relay:

```python
from relay import Relay, Event, Emitter, Listener

class SampleRelay(Relay):
    @Relay.listens
    async def some_listener(self, event: Event[SomeDataModel]): ...

    @Relay.emits
    async def some_emitter(self) -> SomeDataModel:
        ...
        return SomeDataModel(...)
        # or return Relay.NoEmit(SomeDataModel(...))  # if you don't want to emit 
    
    @Relay.emits
    @Relay.listens
    async def unused_emitter_and_listener(self, Event) -> SomeDataModel:
        ...
        if event.data > 10:
            return Relay.Emit(SomeDataModel(...))
        else:
            return SomeDataModel(...)

# NOTE: you can have more classes that extend Relay. They can communicate with each other.

# Create bindings
emitter_binding = Emitter(
    method=SampleRelay.some_emitter, 
    channel="channel1", 
    event_type="event1"
)
listener_binding = Listener(
    method=SampleRelay.some_listener, 
    channel="channel1", 
    event_type="event1"
)

# Use bindings in the Relay initialization
relay = SampleRelay(bindings_config=[emitter_binding, listener_binding])

# Emit an event (in an asyncio loop)
...
await relay.some_emitter()
```

In this example, when `some_emitter()` is called, it will emit an event whose `channel` and `event_type` are `"channel1"` and `"event1"`, respectively. When this event is emitted, `some_listener` will be invoked with the corresponding event instance. Awaiting the `some_emitter` does not block the execution as the event is emitted asynchronously.

## Error Handling

Relay provides robust error handling features. If the data type of the emitting event does not match with the required data type or type hints are missing/inconsistent, a `TypeError` will be raised.

## Full Documentation 

Please note that the Relay package is under development, and the existing functionality may slightly change in future versions.