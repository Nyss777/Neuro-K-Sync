import os
from pathlib import Path
from typing import cast

import hjson
from CF_Program import Song, get_song_data, process_new_tags, set_tags
from create_hjsons import create_payload_from_dict
from engraver import engrave_payload, get_all_mp3
from hash_mutagen import get_audio_hash

LIVE_ARCHIVE_PATH = r'C:\Users\Nyss\Downloads\Anywhere Else'
LOCAL_REPO_LOCATION_PATH = r"C:\Users\Nyss\Documents\Code\Metadata Sync"

def get_all_hjson(directory: str) -> list[str]: 
    """
    Function that gathers all hjson files from a directory.
    """
    p = Path(directory)
    return [(str(f)) for f in p.rglob('*.hjson') if f.is_file()]

def get_changed_files() -> None:
    # make a get_zip instead
    return

def get_metadata(hjson_path: str) -> ( dict[str, (str | int | float)] | None ):
    # 1. Load the HJSON metadata
    try:
        with open(hjson_path, 'r', encoding='utf-8') as f:
            metadata = cast(dict[str, (str | int | float)], hjson.load(f))
        return metadata

    except Exception:
        print(f"Unable to process metadata for {os.path.basename(hjson_path)}!")
        return None


if __name__ == "__main__":

    os.chdir(LOCAL_REPO_LOCATION_PATH)
    
    # changed_files = get_changed_files()
    # print(f"Number of changes: {len(changed_files)}")
    # print(f"DIF-TREE RESPONSE: {changed_files}")

    ## PLACEHOLDER
    changed_files = get_all_hjson(LOCAL_REPO_LOCATION_PATH)

    lookup_table = {metadata["xxHash"] : metadata
                    for file_path in changed_files
                    if file_path.endswith('.hjson')
                    and (metadata := get_metadata(file_path))}

    song_files = get_all_mp3(LIVE_ARCHIVE_PATH)
    print(f"Songs Found: {len(song_files)}")

    for song_path in song_files:
        payload, song_data, _ = get_song_data(song_path)

        xxhash_value = song_data.get("xxHash", None) ## If this is too slow maybe use regex on the payload

        if not xxhash_value:
            xxhash_value = get_audio_hash(song_path)
        if not xxhash_value:
            print(f"Unable to get xxhash for {song_path}")
            continue
        
        hjson_data = lookup_table.get(xxhash_value)

        if not hjson_data:
            continue
        
        copy = False
        for key in hjson_data:
            if song_data[key] != str(hjson_data[key]):
                copy = True
                print(f"They differ in {key}; {song_data[key]} vs {hjson_data[key]}")

        if copy: 

            # this will be different for actual use
            # no backup
            filename = os.path.basename(song_path)
            parent = os.path.basename(os.path.dirname(song_path))

            new_payload = create_payload_from_dict(hjson_data=hjson_data, song_path=song_path, filename=filename)
            engrave_payload(path=song_path, song_data=new_payload) ## side-effect

            song_obj = Song(song_path)
            process_new_tags(song_obj)

            set_tags(song_path, song_obj, None, None) ## side-effect

            if song_obj.filename != os.path.basename(song_path):
                renamed_path = os.path.join(os.path.dirname(song_path), song_obj.filename)
                os.rename(src=song_path, dst=renamed_path) ## side-effect