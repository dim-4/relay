import pytest
from relay.utils import matches_type


class Base:
    pass

class Derived(Base):
    pass

class Unrelated:
    pass


def test_matches_type_with_exact_match():
    obj = Base()
    assert matches_type(obj, Base) == True

def test_matches_type_with_subclass():
    obj = Derived()
    assert matches_type(obj, Base) == True

def test_matches_type_with_unrelated_class():
    obj = Unrelated()
    assert matches_type(obj, Base) == False

def test_matches_type_with_exact_subclass():
    obj = Derived()
    assert matches_type(obj, Derived) == True

def test_matches_type_with_base_as_subclass():
    obj = Base()
    assert matches_type(obj, Derived) == False

def test_matches_type_with_non_class_objects():
    num = 5
    assert matches_type(num, int) == True
    assert matches_type(num, float) == False
    assert matches_type(num, (int, float)) == True  # Checks
