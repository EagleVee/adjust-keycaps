from typing import Any, Dict, List, Tuple, Union
from types import SimpleNamespace
import re

from src.utils.file_utils import safe_get
from src.utils.type_utils import is_type
from functools import reduce

cap_deactivation_colour: str = '#cccccc'
glyph_deactivation_colour: str = '#000000'


def validate_value(key: str, value: Any) -> bool:
    hex_color_pattern = r'^#[a-f0-9]{6}$'
    valid_p_values = {'R1', 'R2', 'R3', 'R4', 'R5', 'SPACE', '', None}

    if key in ['c', 't'] and not re.match(hex_color_pattern, value, re.IGNORECASE):
        print(f"Key {key} must have values of the form: '#' + a six-digit hex value, got {value}")
        return False
    elif key in ['l', 'n', 'd', 'g'] and not isinstance(value, bool):
        print(f"Key {key} must be either true/false, got {value}")
        return False
    elif key == 'p' and value not in valid_p_values:
        print(f"Adjustkeys only recognizes profiles R1-5 and SPACE, got value {value} for p-key")
        return False
    elif key not in ['c', 't', 'l', 'n', 'd', 'g', 'p'] and not isinstance(value, (float, int)):
        print(f"Expected either an integer or a number with a decimal point for key {key}, got {value}")
        return False
    return True


def check_keypart(keypart: Any) -> bool:
    if isinstance(keypart, str):
        return True  # Strings are valid
    if not is_type(keypart, dict, 'The innermost lists of a KLE file must contain only strings and mappings'):
        return False
    return all(validate_value(k, v) for k, v in keypart.items())


def type_check_kle_layout(kle_layout: object) -> bool:
    if not is_type(kle_layout, list, 'KLE layout should be a list at the outermost level'):
        return False

    for line in kle_layout:
        if not is_type(line, (dict, list),
                       'An item in the outermost list of the KLE file is not a dictionary or a list'):
            return False
        if isinstance(line, list) and not all(check_keypart(keypart) for keypart in line):
            return False

    return True


##
# @brief Remove some key from `d` and return the result
#
# @param d:dict A dictionary
# @param k A key to remove
#
# @return A copy of `d` with (k,v) removed
def rem(d: dict, k) -> dict:
    if k not in d:
        print(f'Key {k} not in {d}')
    t = dict(d)
    del t[k]
    return t


def parse_kle_layout(layout: [[dict]], profile_data: dict, use_deactivation_colour: bool) -> [dict]:
    if not type_check_kle_layout(layout):
        raise ValueError('KLE layout failed type-checking, see console for more information')
    print('Reading layout information')

    if type(layout) != list and any(
            list(map(lambda l: type(l) != list, layout))):
        raise ValueError('Expected a list of lists in the layout (see the JSON output of KLE)'
                         )

    profile_row_map: dict = safe_get(profile_data, 'profile-row-map')

    parsed_layout: [dict] = []
    parser_default_state_dict: dict = {
        'c': cap_deactivation_colour if not use_deactivation_colour else None,
        't': glyph_deactivation_colour if not use_deactivation_colour else None,
        'i': 0,
        'x': 0.0,
        'y': 0.0,
        'r': 0.0,
        'rx': 0.0,
        'ry': 0.0,
        'p': profile_row_map['R1'] if profile_row_map is not None else 'R1',
    }
    parser_state: SimpleNamespace = SimpleNamespace(**parser_default_state_dict)
    for line in layout:
        parser_state.x = 0.0
        parser_state.i = 0
        if type(line) != list:
            continue
        while parser_state.i < len(line):
            # Parse for the next key
            print('Handling layout, looking at pair "%s" and "%s"' %
                  (str(line[parser_state.i]).replace('\n', '\\n'),
                   str(safe_get(line, parser_state.i + 1)).replace('\n', '\\n')))
            (shift, line[parser_state.i]) = parse_key(line[parser_state.i], safe_get(line, parser_state.i + 1),
                                                      parser_state, profile_row_map)
            key: dict = line[parser_state.i]

            # Handle colour changes
            parser_state.c = key['cap-style-raw']
            if use_deactivation_colour and parser_state.c == cap_deactivation_colour:
                parser_state.c = None
                key['cap-style-raw'] = None
            parser_state.t = key['glyph-colour-raw']
            if use_deactivation_colour and parser_state.t == glyph_deactivation_colour:
                parser_state.t = None
                key['glyph-colour-raw'] = None

            # Handle shifts
            if 'shift-y' in key:
                parser_state.y += key['shift-y']
                parser_state.x = 0.0
            if 'shift-x' in key:
                parser_state.x += key['shift-x']

            # Handle the profile
            parser_state.p = key['profile-part']

            # Handle the angle
            parser_state.r = key['rotation']
            if 'r' in key or 'rx' in key or 'ry' in key:
                if 'rx' in key:
                    parser_state.rx = key['rx']
                    key = rem(key, 'rx')
                else:
                    parser_state.rx = -key['shift-x'] if 'shift-x' in key else 0.0
                if 'ry' in key:
                    parser_state.ry = key['ry']
                    key = rem(key, 'ry')
                else:
                    parser_state.ry = -key['shift-y'] if 'shift-y' in key else 0.0
                parser_state.x = key['shift-x'] if 'shift-x' in key else 0.0
                parser_state.y = key['shift-y'] if 'shift-y' in key else 0.0

            # Add to layout
            if 'key' in key and (not 'd' in key or not key['d']):
                parsed_layout += [key]

            # Move col to next position
            parser_state.x += key['width']

            # Move to the keycap representation
            parser_state.i += shift
        if len(line) > 1 and 'shift-y' not in line[-1]:
            parser_state.y += 1

    return list(map(add_cap_name, parsed_layout))


def process_string_key(key: str) -> dict:
    """Process a key when it's a string."""
    return {'key': parse_name(key)}


def dict_union(*ds: [dict]) -> dict:
    def _dict_union(a: dict, b: dict) -> dict:
        return dict(a, **b)

    return dict(reduce(_dict_union, ds, {}))


def process_dict_key(key: dict, nextKey: Any) -> Tuple[dict, int]:
    """Process a key when it's a dictionary."""
    if nextKey is not None and isinstance(nextKey, str):
        combined = dict_union(key, {'key': parse_name(nextKey)})
        return combined, 2
    return dict(key), 1


def parse_key(key: Any, nextKey: Any, parser_state: SimpleNamespace, profile_row_map: dict) -> Tuple[int, dict]:
    shift = 1

    if isinstance(key, str):
        ret = process_string_key(key)
    elif isinstance(key, dict):
        ret, shift = process_dict_key(key, nextKey)
    else:
        print('Malformed data when reading %s and %s' % (str(key), str(nextKey)))

    # Apply default values and transformations

    return shift, ret


# Additional functions like `apply_key_type_conditions` and `final_key_checks` should be defined here...

def parse_name(txt: str) -> str:
    return '-'.join(txt.split('\n'))


def add_cap_name(key: dict) -> dict:
    key['cap-name'] = gen_cap_name(key)
    return key


def gen_cap_name(key: dict) -> str:
    if 'key-type' in key:
        return key['key-type']
    else:
        name: str = '%s-%su' % (key['profile-part'], ('%.2f' % float(key['width'])).replace('.', '_'))
        if key['stepped']:
            name += '-%su' % ('%.2f' % float(key['secondary-height'])).replace('.', '_')
            name += '-%su' % ('%.2f' % float(key['secondary-width'])).replace('.', '_')
            name += '-stepped'
        if key['homing']:
            name += '-bar'
        return name
