# Refactored code

from typing import Any, Dict, List, Tuple, Union


def is_type(obj: object, expected_type: type, message: str) -> bool:
    if not isinstance(obj, expected_type):
        print(message)
        return False
    return True


def validate_dict_type(data: Any, message: str) -> Tuple[bool, bool]:
    """Check if the data is a dictionary."""
    is_valid = isinstance(data, dict)
    return (is_valid, message if not is_valid else "")


def validate_key_in_dict(data: Dict, key: str, message: str) -> Tuple[bool, bool]:
    """Check if a key exists in the dictionary."""
    is_valid = key in data
    return (is_valid, message if not is_valid else "")


def validate_value_type(data: Any, expected_type: type, message: str) -> Tuple[bool, bool]:
    """Check if the value is of the expected type."""
    is_valid = isinstance(data, expected_type)
    return (is_valid, message if not is_valid else "")


def check_color_rule_keys(rule: Dict) -> bool:
    """Check required keys in color rule."""
    required_keys = ['name', 'cond', 'cap-style', 'glyph-style']
    missing_keys = [key for key in required_keys if key not in rule]
    if missing_keys:
        print(f"Color map rule missing keys: {', '.join(missing_keys)}")
        return False
    return True


def has_key_and_check_type(dictionary: dict, key: str, expected_type: type, type_message: str,
                           missing_key_message: str) -> bool:
    if key not in dictionary:
        print(missing_key_message)
        return False
    if not isinstance(dictionary[key], expected_type):
        print(type_message.format(key))
        return False
    return True
