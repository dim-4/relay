import pytest

from relay.bindings import Binding, Listener, Emitter, SourceInfo
from relay.consts import DEFAULT_CHANNEL, DEFAULT_EVENT_TYPE
from relay.event import FORBIDDEN_CHARACTERS

# 1. Basic Instantiation

def sample_func():
    pass

def test_listener_instantiation():
    sub = Listener(method=sample_func)
    assert isinstance(sub, Listener)

def test_emission_instantiation():
    emit = Emitter(method=sample_func)
    assert isinstance(emit, Emitter)

# 2. Defaults

def test_listener_defaults():
    sub = Listener(method=sample_func)
    assert sub.event_type == DEFAULT_EVENT_TYPE
    assert sub.channel == DEFAULT_CHANNEL
    assert sub.source is None

def test_emission_defaults():
    emit = Emitter(method=sample_func)
    assert emit.event_type == DEFAULT_EVENT_TYPE
    assert emit.channel == DEFAULT_CHANNEL

# 3. Validation

def test_listener_invalid_handler():
    with pytest.raises(ValueError):
        Listener(method="not_a_callable")

def test_emission_invalid_emitter():
    with pytest.raises(ValueError):
        Emitter(method="not_a_callable")

# 4. Forbidden Characters

def test_forbidden_characters_in_bindings():
    for char in FORBIDDEN_CHARACTERS:
        with pytest.raises(ValueError, match=f"Forbidden character '{char}'"):
            Listener(method=sample_func, channel=f"channel{char}")
            
        with pytest.raises(ValueError, match=f"Forbidden character '{char}'"):
            Listener(method=sample_func, event_type=f"event{char}")
            
        with pytest.raises(ValueError, match=f"Forbidden character '{char}'"):
            Emitter(method=sample_func, channel=f"channel{char}")
            
        with pytest.raises(ValueError, match=f"Forbidden character '{char}'"):
            Emitter(method=sample_func, event_type=f"event{char}")
