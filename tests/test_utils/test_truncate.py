import pytest
from relay.utils import truncate

def test_basic_truncation():
    """Test basic string truncation."""
    data = "This is a long string that needs truncation."
    result = truncate(data, 20)
    assert result == "This is a long st..."

def test_truncation_with_braces():
    """Test truncation when data starts with an opening brace."""
    data = "{key: value, another_key: another_value}"
    result = truncate(data, 20)
    assert result == "{key: value, ano...}"

def test_no_truncation_needed():
    """Test string that doesn't require truncation."""
    data = "Short string"
    result = truncate(data, 20)
    assert result == "Short string"

def test_default_truncation_length():
    """Test default truncation length."""
    data = "A string that will be truncated at the default length."
    result = truncate(data)
    assert result == "A string that wil..."

def test_truncation_with_different_data_types():
    """Test truncation with various data types."""
    integer_data = 123456789012345678901
    result = truncate(integer_data)
    assert result == "12345678901234567..."
    
    list_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    result = truncate(list_data, 15)
    assert result == "[1, 2, 3, 4...]"

    tuple_data = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    result = truncate(tuple_data, 15)
    assert result == "(1, 2, 3, 4...)"
