# import pytest

# from relay import Relay


# class SomeRelay(Relay):

#     @Relay.emits
#     def func_without_type():
#         return "Hello"



# def test_emits_no_return_type_hint():
#     some_relay = SomeRelay()

#     with pytest.raises(TypeError):

#     func_without_type()

# def test_emits_incorrect_return_type():
#     with pytest.raises(TypeError):
#         @emits
#         def func_with_incorrect_return_type() -> int:
#             return "Hello"

#     func_with_incorrect_return_type()

# def test_emits_incorrect_data_structure():
#     SomeRelay.bindings[("test_channel", "test_event")] = str  # Expecting str

#     with pytest.raises(TypeError):
#         @emits
#         def func_with_incorrect_structure() -> list:
#             return ["Hello", "World"]

#     func_with_incorrect_structure()

# def test_emits_correctly():
#     SomeRelay.bindings[("test_channel", "test_event")] = str  # Expecting str

#     @emits
#     def correct_func() -> str:
#         return "Hello"

#     # Shouldn't raise any error
#     correct_func()