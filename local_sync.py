import os
import zipfile
from pathlib import Path
from typing import cast

import hjson
from CF_Program import Song, get_song_data, process_new_tags, set_tags
from create_hjsons import create_payload_from_dict
from engraver import engrave_payload, get_all_mp3
from hash_mutagen import get_audio_hash

LIVE_ARCHIVE_PATH = r'C:\Users\Nyss\Downloads\testt'
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

def get_metadata_from_zip(zip_ref: zipfile.ZipFile, hjson_path: str) -> ( dict[str, (str | int | float)] | None ):
    # 1. Load the HJSON metadata
    # try:
    with zip_ref.open(hjson_path, 'r') as f:
        content = f.read().decode('utf-8')
        metadata = cast(dict[str, (str | int | float)], hjson.loads(content))
    return metadata

    # except Exception:
    #     print(f"Unable to process metadata for {os.path.basename(hjson_path)}!")
    #     return None


if __name__ == "__main__":

    # os.chdir(LOCAL_REPO_LOCATION_PATH)
    
    # changed_files = get_changed_files()
    # print(f"Number of changes: {len(changed_files)}")
    # print(f"DIF-TREE RESPONSE: {changed_files}")

    ## PLACEHOLDER
    with zipfile.ZipFile("zipped_metadata.zip") as zip_ref:
        changed_files = zip_ref.namelist()

        lookup_table = {metadata["xxHash"] : metadata
                        for file_path in changed_files
                        if file_path.endswith('.hjson')
                        and (metadata := get_metadata_from_zip(zip_ref, file_path))}

    # print(f"Number of changes: {len(changed_files)}")
    # print(f"DIF-TREE RESPONSE: {changed_files}")


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
            print(f"no json data for {song_path}")
            continue
        
        copy = False
        for key in hjson_data:
            if song_data.get(key, "") != str(hjson_data[key]):
                copy = True
                print(f"They differ in {key}; {song_data.get(key, "")} vs {hjson_data[key]}")

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
                renamed_path = Path(os.path.join(os.path.dirname(song_path), song_obj.filename))
                tries = 0

                while renamed_path.is_file():
                    if tries:
                        new_stem = renamed_path.stem[:-(len(str(tries)) + 2)] + f"({tries})"
                        tries += 1
                        
                    else:
                        tries += 1
                        new_stem = renamed_path.stem + ' (1)'

                    renamed_path = renamed_path.with_stem(new_stem)

                os.rename(src=song_path, dst=renamed_path) ## side-effect
