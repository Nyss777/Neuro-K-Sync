import sys

import pytest

sys.path.append(r'C:\Users\Nyss\Documents\Code\Python\Neuro_karaoke\Local_Synch')

from local_sync import get_raw


@pytest.fixture
def raw_json():
    return '{"Date":"2023-04-26","Title":"Sound of Silence","Artist":"Disturbed","CoverArtist":"Neuro","Version":"1","Discnumber":"1","Track":"89/98","Comment":"None","Special":"0","xxHash":"1234"}'

@pytest.mark.parametrize("key, expected", [
    ("Title", "Sound of Silence"),
    ("Artist", "Disturbed"),
    ("Version", "1"),
    ("xxHash", "1234"),
    ("NonExistentKey", ""),  # Assuming your function returns None for missing 
    ("Sound of Silence", "")
])
def test_get_raw_valid_keys(raw_json, key, expected):
    """Test that all standard keys return the correct string values."""
    assert get_raw(raw_json, key) == expected

@pytest.mark.parametrize("custom_json, key, expected", [
    ('{"Special":"0"}', "Special", "0"),           # Integer to string conversion
    ('{"Comment": ""}', "Comment", ""),           # Empty string
    ('{"Empty": null}', "Empty", ""),           # JSON null handling
])
def test_get_raw_edge_cases(custom_json, key, expected):
    assert get_raw(custom_json, key) == expected