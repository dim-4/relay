import pytest
from pydantic import BaseModel, ValidationError
from typing import Union, List, Tuple, Set, Dict, Literal, Callable, get_origin, get_args
import collections.abc as abc
from relay.utils import type_check

# Test for Basic Types and User-Defined Classes
@pytest.mark.parametrize("value, type_hint, expected", [
    (5, int, True),
    ("hello", str, True),
    (5.0, float, True),
    ("hello", int, False),
    (5, str, False),
    (5.0, str, False),
    (None, int, False),
    (5, None, False),
    (None, None, True),
])
def test_basic_types(value, type_hint, expected):
    assert type_check(value, type_hint) == expected

class User:
    def __init__(self, name):
        self.name = name

class Bob(BaseModel):
    name: str

@pytest.mark.parametrize("value, type_hint, expected", [
    (User("Alice"), User, True),
    ("Alice", User, False),
    (Bob(name="Bob"), Bob, True),
    ("Bob", Bob, False),
    (Bob(name="Bob"), None, False),
])
def test_user_defined_classes(value, type_hint, expected):
    assert type_check(value, type_hint) == expected

# Define a Pydantic model for testing
class Item(BaseModel):
    name: str
    price: float

# Test for Pydantic's BaseModel
@pytest.mark.parametrize("value, type_hint, expected", [
    ({"name": "apple", "price": 0.5}, Item, False),
    ({"name": "apple"}, Item, False),
    (5, Item, False),
    ("apple", Item, False)
])
def test_pydantic_base_model(value, type_hint, expected):
    try:
        assert type_check(value, type_hint) == expected
    except ValidationError:
        assert not expected

# Test for Typing Constructs - List, Tuple, Set, Dict
@pytest.mark.parametrize("value, type_hint, expected", [
    ([], list, True),
    ((), tuple, True),
    ([], list[int], True),
    ((), tuple[int], True),
    ({}, dict, True),
    ({}, dict[str, int], True),
    ({}, dict[str, list[str, int, dict]], True),
    (set(), set, True),
    (set(), set[int], True),
    ([1, 2, 3], list[int], True),
    ([1, 2, 3], List[int], True),
    ([1, "2", 3], list[int], False),
    ([1, "2", 3], List[int], False),
    ([1, 2, 3], list[str], False),
    ([1, 2, 3], List[str], False),
    ([1, [2, 3], [4, 5]], list[list[int]], False),
    ([1, [2, 3], [4, 5]], List[List[int]], False),
    ([1, [2, "3"], [4, 5]], list[list[int]], False),
    ([1, [2, "3"], [4, 5]], List[List[int]], False),
    ((1, 2, 3), tuple[int, int, int], True),
    ((1, 2, 3), Tuple[int, int, int], True),
    ((1, "2", 3), tuple[int, str, int], True),
    ((1, "2", 3), Tuple[int, str, int], True),
    ([1, "2", 3], list[int, str, int], True),
    ([1, "2", 3], list[int, str, int], True),
    ((1, 2, 3), tuple[int, int], False),
    ((1, 2, 3), Tuple[int, int], False),
    ({1, 2, 3}, set[int], True),
    ({1, 2, 3}, Set[int], True),
    ({1, "2", 3}, set[int], False),
    ({1, "2", 3}, Set[int], False),
    ({"a": 1, "b": 2}, dict[str, int], True),
    ({"a": 1, "b": 2}, Dict[str, int], True),
    ({"a": 1, "b": "2"}, dict[str, int], False),
    ({"a": 1, "b": "2"}, Dict[str, int], False),
    ({"a": 1, 2: "b"}, dict[int|str, int|str], True),
    ({"a": 1, 2: "b"}, Dict[Union[int, str], Union[int, str]], True)
])
def test_typing_constructs(value, type_hint, expected):
    type_check(value, type_hint) == expected
    assert type_check(value, type_hint) == expected

# Test for Typing Constructs - Union, Literal, Callable
@pytest.mark.parametrize("value, type_hint, expected", [
    (1, Union[int, str], True),
    (1, int|str, True),
    ("hello", Union[int, str], True),
    (1.0, Union[int, str], False),
    ("apple", Literal["apple", "banana"], True),
    ("cherry", Literal["apple", "banana"], False),
    (lambda x: x+1, Callable, True),
    ("not_callable", Callable, False),
])
def test_union_literal_callable(value, type_hint, expected):
    assert type_check(value, type_hint) == expected

# Test for Errors - ValidationError, TypeError, NotImplementedError
def test_error_cases():

    # TypeError
    unsupported_type = "unsupported_type"
    with pytest.raises(TypeError) as e:
        type_check(5, unsupported_type)
    assert str(e.value) == f"Type '{unsupported_type}' is not supported."
    
    # NotImplementedError
    with pytest.raises(NotImplementedError) as e:
        type_check(lambda x, y: x+y, Callable[[int, str], bool])
    assert (str(e.value) == "Callable type hints with parameters "
            "(ex: Callable[[int, str], bool]) are not supported yet.")
