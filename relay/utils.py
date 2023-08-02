from collections import abc
from pydantic import BaseModel, ValidationError
from types import UnionType
from typing import Any, Callable, get_args, get_origin, Literal, Union


def truncate(data:Any, length:int=20) -> str:
    """
    Truncate the string representation of data if it's longer than the 
    specified length. Append "..." to the end of the truncated string. 
    If the data starts with an opening brace, append the matching closing 
    brace after "...".
    
    Args:
    ----
    - `data` (`Any`): The data to truncate.
    - `length` (`int`, `optional`): The maximum length of the string 
      representation. Defaults to 20.

    Returns:
    -------
    str
        The truncated string representation of the data.
    """
    data_repr = str(data)
    matches = {"{": "}", "[": "]", "(": ")", "<": ">"}
    end = "..."
    
    if len(data_repr) > length:
        # If data starts with an opening brace, update the ending to 
        # include the matching closing brace.
        if data_repr[0] in matches:
            end += matches[data_repr[0]]
        return f"{data_repr[:length-len(end)]}{end}"
    else:
        return data_repr

def type_check(value:Any, type_hint:BaseModel|Any) -> bool:
    """
    Checks if the given value matches the expected type hint.

    This function is designed to handle a wide variety of type hints, 
    including those from the `typing` module, Pydantic's BaseModel, and 
    other base types. For Pydantic's BaseModel subclasses, the function 
    leverages Pydantic's internal validation to determine type compatibility.

    Parameters:
    ----------
    - value (Any): The value to be type-checked.
    - type_hint (BaseModel|Any): The expected type hint for the value. 
      This can be a basic type like int or str, a subclass of BaseModel, or 
      a more complex type hint from the `typing` module such as List[int] 
      or Union[str, int].

    Returns:
    -------
    - bool: True if the value matches the type hint, False otherwise.

    Supported type hints include:
    - Basic Python types: int, str, float, etc.
    - Pydantic's BaseModel subclasses.
    - User defined classes.
    - Typing constructs: Union, Literal.
    - May be extended to support more complex type hints in the future.

    Notes:
    -----
    - When checking against Pydantic's BaseModel, the function attempts to
      parse the value using the model's `parse_obj` method. If successful, the 
      value matches the type hint.
    - For Callable type hints, only unparameterized checks (e.g., `Callable`) 
      are supported. Parameterized versions (e.g., `Callable[[int, str], bool]`) 
      are not yet implemented.

    Raises:
    ------
    - ValidationError: If the value does not match a BaseModel type hint.
    - TypeError: If the provided type hint is not supported.
    - NotImplementedError: If the function encounters an unsupported 
      parameterized Callable type hint.
    """
    if type_hint is Any:
        return True
    
    if value is None and type_hint in (None, type(None)):
        return True
    if value is not None and type_hint in (None, type(None)):
        return False

    # If the type_hint is a subclass of BaseModel, use Pydantic's validation
    if issubclass(type(type_hint), BaseModel):
        try:
            type_hint.parse_obj(value)
            return True
        except ValidationError:
            return False

    origin = get_origin(type_hint)

    # for basic types (int, str, etc.) and user-defined classes
    if not origin:
        try:
            return isinstance(value, type_hint)
        except:
            raise TypeError(f"Type '{type_hint}' is not supported.")

    # Handle List[type] or List[List[type]] and so on
    if origin == list:
        args = get_args(type_hint)
        # If no type argument is provided for List, accept any list
        if not args:
            return isinstance(value, list)
        if not isinstance(value, list):
            return False
        if len(args) == 1:
            if len(value) == 0:
                return True
            return all(type_check(item, args[0]) for item in value)
        if len(args) != len(value):
            return False
        return all(type_check(item, arg) for item, arg in zip(value, args))
   
    # Handle Tuple[type, ...] or Tuple[Tuple[type, ...], ...] and so on
    if origin == tuple:
        args = get_args(type_hint)
        # If no type arguments are provided for Tuple, accept any tuple
        if not args:
            return isinstance(value, tuple)
        if not isinstance(value, tuple):
            return False
        if len(args) == 1:
            if len(value) == 0:
                return True
            return all(type_check(item, args[0]) for item in value)
        # Check if the tuple length matches the length of the type hint
        if len(args) != len(value):
            return False
        return all(type_check(item, arg) for item, arg in zip(value, args))

    # Handle Set[type] or Set[Set[type]] and so on
    if origin == set:
        args = get_args(type_hint)
        return (isinstance(value, set) and 
                all(type_check(item, args[0]) for item in value))

    # Handle Dict[key_type, val_type] and so on
    if origin == dict:
        key_type, val_type = get_args(type_hint)
        return (isinstance(value, dict) and 
                all(isinstance(k, key_type) and 
                    type_check(v, val_type) for k, v in value.items()))

    # Handle Union types (which includes Optional)
    if origin is UnionType or origin is Union:
        allowed_types = get_args(type_hint)
        return any(type_check(value, t) for t in allowed_types)

    # Handle Literal types
    if origin == Literal:
        allowed_values = get_args(type_hint)
        return value in allowed_values

    # Handle Callable types
    if origin == abc.Callable:
        args = get_args(type_hint)
        # Check if Callable is parameterized i.e. Callable[[int, str], bool]
        if args == ():
            return callable(value)
        raise NotImplementedError("Callable type hints with parameters "
                                  "(ex: Callable[[int, str], bool]) "
                                  "are not supported yet.")

    # Add more complex type checks as needed

    raise TypeError(f"Type '{type_hint}' is not supported.")
    # return False

def validate_forbidden_characters(value: str, forbidden_chars:list[str]) -> str:
    """
    Validate if the given value contains forbidden characters.
    
    Raises:
    ------
        ValueError: If forbidden characters are found in the value.
        
    Returns:
    -------
        The original value if no forbidden characters are found.
    """
    for char in forbidden_chars:
        if char in str(value):
            raise ValueError(f"Forbidden character '{char}' in channel or "
                             "event_type. Please avoid using any of the "
                             f"following chars: {forbidden_chars}")
    return value
