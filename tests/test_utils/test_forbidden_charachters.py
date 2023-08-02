import pytest

from relay.utils import validate_forbidden_characters as validate_chars
from relay.consts import FORBIDDEN_CHARACTERS

def test_make_sure_colon_is_forbidden():
    """ Ensure colon is in the forbidden characters list. """
    assert ":" in FORBIDDEN_CHARACTERS, ("Colon is expected to be forbidden. "
                                         "If not, make sure to update tests.")

def test_valid_string():
    """ Ensure no exception for valid strings. """
    assert validate_chars("validString", FORBIDDEN_CHARACTERS) == "validString"

@pytest.mark.parametrize("forbidden_char", FORBIDDEN_CHARACTERS)
def test_forbidden_characters(forbidden_char):
    """ Test individual forbidden characters. """
    with pytest.raises(ValueError, match="Forbidden character") as exc_info:
        validate_chars(f"This has a {forbidden_char} character",
                       forbidden_chars=FORBIDDEN_CHARACTERS)

    assert str(forbidden_char) in str(exc_info.value)

def test_combined_forbidden_characters():
    """ Test a string containing multiple forbidden characters. """
    test_string = "".join(FORBIDDEN_CHARACTERS)
    with pytest.raises(ValueError, match="Forbidden character"):
        validate_chars(test_string, forbidden_chars=FORBIDDEN_CHARACTERS)

def test_non_string_input():
    """ Ensure the function works with non-string inputs. """
    number_without_forbidden = 12345
    assert (validate_chars(number_without_forbidden, 
                           forbidden_chars=FORBIDDEN_CHARACTERS) 
            == number_without_forbidden)

    number_with_forbidden = f"123:{FORBIDDEN_CHARACTERS[0]}45"
    with pytest.raises(ValueError, match="Forbidden character"):
        validate_chars(number_with_forbidden, 
                       forbidden_chars=FORBIDDEN_CHARACTERS)
