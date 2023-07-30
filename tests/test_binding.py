import pytest

from relay.binding import Subscription, Emission, SourceInfo
from relay.consts import DEFAULT_CHANNEL, DEFAULT_EVENT_TYPE

# 1. Basic Instantiation

def sample_func():
    pass

def test_subscription_instantiation():
    sub = Subscription(handler=sample_func)
    assert isinstance(sub, Subscription)

def test_emission_instantiation():
    emit = Emission(emitter=sample_func)
    assert isinstance(emit, Emission)

# 2. Defaults

def test_subscription_defaults():
    sub = Subscription(handler=sample_func)
    assert sub.event_type == DEFAULT_EVENT_TYPE
    assert sub.channel == DEFAULT_CHANNEL
    assert sub.source is None

def test_emission_defaults():
    emit = Emission(emitter=sample_func)
    assert emit.event_type == DEFAULT_EVENT_TYPE
    assert emit.channel == DEFAULT_CHANNEL

# 3. Validation

def test_subscription_invalid_handler():
    with pytest.raises(ValueError):
        Subscription(handler="not_a_callable")

def test_emission_invalid_emitter():
    with pytest.raises(ValueError):
        Emission(emitter="not_a_callable")
