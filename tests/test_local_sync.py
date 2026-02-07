import pytest
from local_sync.local_sync import get_raw


@pytest.fixture
def raw_json():
    return '{"Date":"2023-04-26","Title":"Sound of Silence","Artist":"Disturbed","CoverArtist":"Neuro","Version":"1","Discnumber":"1","Track":"89/98","Comment":"None","Special":"0","xxHash":"1234"}'

@pytest.fixture
def fnaf_json():
    return """{"Date":"2023-08-01","Title":"It's Been So Long","Artist":"The Living Tombstone","CoverArtist":"Neuro","Version":"3","Discnumber":"3","Track":"70/283","Comment":"STOP POSTING ABOUT fnaf.mp3 IM TIRED OF SEEING IT. MY FRIENDS ON GITHUB SEND ME ISSUE TICKETS, ON DISCORD ITS FUCKING ISSUE TICKETS! I was in the Thread, right? and AAAALL OF THE RECENT MESSAGES were just fnaf.mp3. I-I showed my karaoke archive to Pb and t-the tags I opened it and I said 'hey Pb, it only says 2023! HAHA ITS BEEEEN SO LOOOOONG SINCE I LAST HAVE SEEN MY SON LOST TO THIS MONSTER, TO THE MAN BEHIND THE SLAUGHTERR","Special":"0","xxHash":"f3395adc789baf3b"}"""

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

@pytest.mark.parametrize("key, expected", [
    ("Title", "It's Been So Long"),
    ("Artist", "The Living Tombstone"),
    ("Version", "3"),
    ("xxHash", "f3395adc789baf3b"),
    ("NonExistentKey", ""),  # Assuming your function returns None for missing 
    ("Sound of Silence", "")
])
def test_get_raw_fnaf_valid_keys(fnaf_json, key, expected):
    """Test that all standard keys return the correct string values."""
    assert get_raw(fnaf_json, key) == expected

@pytest.mark.parametrize("custom_json, key, expected", [
    ('{"Special": 0}', "Special", ""),           
    ('{"Comment": ""}', "Comment", ""),          
    ('{"Empty": null}', "Empty", ""),       
])
def test_get_raw_edge_cases(custom_json, key, expected):
    assert get_raw(custom_json, key) == expected