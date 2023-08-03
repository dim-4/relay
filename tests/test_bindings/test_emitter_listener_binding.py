import pytest

from pydantic import ValidationError
from relay.bindings import Binding, Listener, Emitter, SourceInfo
from relay.consts import DEFAULT_CHANNEL, DEFAULT_EVENT_TYPE
from relay.event import FORBIDDEN_CHARACTERS

# 1. Basic Instantiation

async def sample_async_func():
    pass

def sample_sync_func():
    pass

def test_listener_instantiation():
    sub = Listener(method=sample_async_func)
    assert isinstance(sub, Listener)

def test_emission_instantiation():
    emit = Emitter(method=sample_async_func)
    assert isinstance(emit, Emitter)

# 2. Defaults

def test_listener_defaults():
    sub = Listener(method=sample_async_func)
    assert sub.event_type == DEFAULT_EVENT_TYPE
    assert sub.channel == DEFAULT_CHANNEL
    assert sub.source is None

def test_emission_defaults():
    emit = Emitter(method=sample_async_func)
    assert emit.event_type == DEFAULT_EVENT_TYPE
    assert emit.channel == DEFAULT_CHANNEL

# 3. Validation

def test_listener_invalid_handler():
    with pytest.raises(ValidationError):
        Listener(method="not_a_callable")

def test_emission_invalid_emitter():
    with pytest.raises(ValidationError):
        Emitter(method="not_a_callable")

# 4. Forbidden Characters

def test_forbidden_characters_in_bindings():
    for char in FORBIDDEN_CHARACTERS:
        with pytest.raises(ValueError, match=f"Forbidden character '{char}'"):
            Listener(method=sample_async_func, channel=f"channel{char}")
            
        with pytest.raises(ValueError, match=f"Forbidden character '{char}'"):
            Listener(method=sample_async_func, event_type=f"event{char}")
            
        with pytest.raises(ValueError, match=f"Forbidden character '{char}'"):
            Emitter(method=sample_async_func, channel=f"channel{char}")
            
        with pytest.raises(ValueError, match=f"Forbidden character '{char}'"):
            Emitter(method=sample_async_func, event_type=f"event{char}")

# 5. Sync function test
def test_sync_method():
    with pytest.raises(TypeError, match="The method must be asynchronous."):
        sub = Listener(method=sample_sync_func)
    
    with pytest.raises(TypeError, match="The method must be asynchronous."):
        emit = Emitter(method=sample_sync_func)
