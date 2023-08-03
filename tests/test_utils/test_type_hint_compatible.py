import pytest
from pydantic import BaseModel
from typing import Dict, List, Set, Tuple, Union, Any
from relay.utils import type_hint_compatible


# Define some example BaseModel subclasses for testing purposes:
class Person(BaseModel):
    name: str
    age: int

class Employee(Person):
    role: str

class Student(Person):
    school: str

class Animal(BaseModel):
    name: str
    species: str
    age: int

class Building:
    pass

class School(Building):
    pass

class House(Building):
    pass


# Pytest for type_hint_compatible:
# skip
@pytest.mark.skip(reason="Not implemented/used yet.")
def test_type_hint_compatible():
    # Basic compatibility tests
    assert type_hint_compatible(int, int)
    assert not type_hint_compatible(int, str)

    assert type_hint_compatible(int, int|str)
    assert type_hint_compatible(int|str, int)
    assert type_hint_compatible(int, Union[int, str])
    assert type_hint_compatible(Union[int, str], int)

    assert type_hint_compatible(int|str, int|str|float)
    assert type_hint_compatible(int|str|float, int|str)
    assert type_hint_compatible(Union[int, str], Union[int, str, float])
    assert type_hint_compatible(Union[int, str, float], Union[int, str])

    assert type_hint_compatible(int|float, int|str)
    assert type_hint_compatible(int|str, int|float)
    assert type_hint_compatible(Union[int, float], Union[int, str])
    assert type_hint_compatible(Union[int, str], Union[int, float])

    assert not type_hint_compatible(int|float, str|dict)
    assert not type_hint_compatible(str|dict, int|float)
    assert not type_hint_compatible(Union[int, float], Union[str, dict])
    assert not type_hint_compatible(Union[str, dict], Union[int, float])

    # Nested types
    assert type_hint_compatible(list[int], list)
    assert type_hint_compatible(list, list[int])
    assert type_hint_compatible(List[int], list)
    assert type_hint_compatible(list, List[int])
    assert type_hint_compatible(List[int], List)
    assert type_hint_compatible(List, List[int])
    assert not type_hint_compatible(list[int], list[str])
    assert not type_hint_compatible(list[str], list[int])
    assert not type_hint_compatible(list[int|str], list[float|bool])

    assert type_hint_compatible(list[int], list[int]|str)
    assert type_hint_compatible(list[int]|str, list[int])
    assert type_hint_compatible(List[int], list[int]|str)
    assert type_hint_compatible(list[int]|str, List[int])
    assert type_hint_compatible(List[int], List[int]|str)
    assert type_hint_compatible(List[int]|str, List[int])
    assert type_hint_compatible(list[int], Union[list[int], str])
    assert type_hint_compatible(Union[list[int], str], list[int])
    assert type_hint_compatible(list[int, str, int], list)
    assert not type_hint_compatible(list[int, str, int], list[str, int, str])
    assert not type_hint_compatible(list[int, str, int], list[int, str])
    assert not type_hint_compatible(list[int], list[str]|str|set|list[set])
    assert not type_hint_compatible(list[int], Union[list[str], str])

    assert type_hint_compatible(tuple[int], tuple)
    assert type_hint_compatible(tuple, tuple[int])
    assert type_hint_compatible(Tuple[int], tuple)
    assert type_hint_compatible(tuple, Tuple[int])
    assert type_hint_compatible(tuple[int, str], tuple)
    assert type_hint_compatible(tuple, tuple[int, str])
    assert type_hint_compatible(Tuple[int, str], tuple)
    assert type_hint_compatible(tuple, Tuple[int, str])
    assert not type_hint_compatible(tuple[int, str], tuple[str, int])
    assert not type_hint_compatible(tuple[str, int], tuple[int, str])
    assert not type_hint_compatible(tuple[int, str], tuple[int, str, int])
    assert not type_hint_compatible(tuple[int, str, int], tuple[int, str])

    assert type_hint_compatible(dict[str, int], dict)
    assert type_hint_compatible(dict, dict[str, int])
    assert type_hint_compatible(Dict[str, int], Dict)
    assert type_hint_compatible(Dict, Dict[str, int])
    assert type_hint_compatible(dict[str, int], dict[str, int]|str)
    assert type_hint_compatible(dict[str, dict], dict[str, dict[str, int]])
    assert type_hint_compatible(dict[str, dict[str, int]], dict[str, dict])
    assert not type_hint_compatible(dict[str, int], dict[str, str])
    assert not type_hint_compatible(dict[str, dict[str, int]], 
                                    dict[str, dict[str, str]])

    assert type_hint_compatible(set[int], set)
    assert type_hint_compatible(set, set[int])
    assert type_hint_compatible(Set[int], Set)
    assert type_hint_compatible(Set, Set[int])
    assert type_hint_compatible(set[int], Set)
    assert type_hint_compatible(set[int|str], set)
    assert type_hint_compatible(set[int|str], Set)
    assert type_hint_compatible(Set[int|str], set)
    assert type_hint_compatible(Set[int|str], Set)
    assert not type_hint_compatible(set[int], set[str])

    # Any
    assert type_hint_compatible(Any, int)
    assert type_hint_compatible(int, Any)
    assert type_hint_compatible(Any, Any)
    assert type_hint_compatible(list[Any], list[str])
    assert type_hint_compatible(dict[str, Any], dict[str, int])
    assert not type_hint_compatible(list[Any], dict[str, dict])

    # Pydantic BaseModel subclasses
    assert type_hint_compatible(Person, Person)
    assert type_hint_compatible(Employee, Person)
    assert type_hint_compatible(Student, Person)
    assert type_hint_compatible(Person, Employee)
    assert type_hint_compatible(Person, Student)
    assert not type_hint_compatible(Employee, Student)
    assert not type_hint_compatible(Student, Employee)
    assert not type_hint_compatible(Person, Animal)
    assert not type_hint_compatible(Animal, Person)
    assert not type_hint_compatible(Employee, Animal)
    assert not type_hint_compatible(Animal, Employee)

    assert type_hint_compatible(Person|Animal, Person)
    assert type_hint_compatible(Person, Person|Animal)
    assert type_hint_compatible(Person|Animal, Employee)

    assert type_hint_compatible(list[Person], list)
    assert type_hint_compatible(list, list[Person])
    assert type_hint_compatible(List[Person], list)
    assert type_hint_compatible(list, List[Person])
    assert type_hint_compatible(List[Person], List)
    assert type_hint_compatible(List, List[Person])
    assert type_hint_compatible(list[Person], list[Employee])
    assert type_hint_compatible(list[Person], list[Student])
    assert type_hint_compatible(list[Employee], list[Person])
    assert type_hint_compatible(list[Student], list[Person])
    assert not type_hint_compatible(list[Employee], list[Student])
    assert not type_hint_compatible(list[Student], list[Employee])
    assert not type_hint_compatible(list[Person], list[Animal])
    assert not type_hint_compatible(list[Animal], list[Person])

    assert type_hint_compatible(list[dict[str, Person]], list)
    assert type_hint_compatible(list, list[dict[str, Person]])
    assert type_hint_compatible(list[dict[str, Person]], list[dict])
    assert type_hint_compatible(list[dict[str, Any]], list[dict[str, Person]])

    # User-defined classes
    assert type_hint_compatible(Building, Building)
    assert type_hint_compatible(School, Building)
    assert type_hint_compatible(House, Building)
    assert type_hint_compatible(Building, School)
    assert type_hint_compatible(Building, House)
    assert not type_hint_compatible(School, House)
    assert not type_hint_compatible(House, School)
    assert not type_hint_compatible(Building, Animal)
    assert not type_hint_compatible(Animal, Building)
    assert not type_hint_compatible(School, Animal)
    assert not type_hint_compatible(Animal, School)

    assert type_hint_compatible(list[Building], list)
    assert type_hint_compatible(list, list[Building])
    assert type_hint_compatible(set[Building], set[Animal]|set[Person|Any])




