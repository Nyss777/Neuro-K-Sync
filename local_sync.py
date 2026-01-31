import io
import os
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import hjson
import requests
from CF_Program import Song, get_song_data, process_new_tags, set_tags
from create_hjsons import create_payload_from_dict
from DF_formatter import apply_in_background, load_preset
from engraver import engrave_payload, get_all_mp3
from file_manager import FileManager
from hash_mutagen import get_audio_hash

LIVE_ARCHIVE_PATH = r'C:\Users\Nyss\Downloads\testt'
LOCAL_REPO_LOCATION_PATH = r"C:\Users\Nyss\Documents\Code\Metadata Sync"

def get_all_json(directory: Path | str) -> list[str]: 
    """
    Function that gathers all hjson files from a directory.
    """
    p = Path(directory)
    return [(str(f)) for f in p.rglob('*.json') if f.is_file()]

def format_tags(path: str, song_obj: Song) -> None:
    if not DF_format(path):
        set_tags(song_path, song_obj, None, None)

def DF_format (file_path: str) -> bool:
    """
    Function for formatting a song with a DF preset
    """

    if getattr(sys, 'frozen', False):
        script_dir = Path(sys.executable).parent
    else:
        script_dir = Path(__file__).parent.absolute()

    if not script_dir.is_dir():
        return False

    presets = get_all_json(script_dir)

    if not presets:
        return False

    try :
        preset = load_preset(presets[0])
        apply_in_background(file_path=file_path, fm=FileManager(), preset=preset)

    except Exception as e:
        print(e)
        return False

    finally:
        return True

def get_all_hjson(directory: str) -> list[str]: 
    """
    Function that gathers all hjson files from a directory.
    """
    p = Path(directory)
    return [(str(f)) for f in p.rglob('*.hjson') if f.is_file()]

def get_remote_zip() -> io.BytesIO | None:
    url = "https://github.com/Nyss777/Neuro-Karaoke-Archive-Metadata/raw/main/zipped_metadata.zip"
    response = requests.get(url)

    if response.status_code == 200:
        # Wrap the bytes in a "BytesIO" object
        zip_in_memory = io.BytesIO(response.content)
        
        return zip_in_memory
    
    return None

def get_metadata_from_zip(zip_ref: zipfile.ZipFile, hjson_path: str) -> dict[str, str|int|float] | None:
    # 1. Load the HJSON metadata
    try:
        with zip_ref.open(hjson_path, 'r') as f:
            content = f.read().decode('utf-8')
            metadata = cast(dict[str, str|int|float], hjson.loads(content))
        return metadata

    except Exception:
        print(f"Unable to process metadata for {os.path.basename(hjson_path)}!")
        return None

@dataclass
class Hjson_Struct:
    metadata: dict[str, str | int | float]
    seen: bool

if __name__ == "__main__":

    zip_data = get_remote_zip()

    if zip_data is None:
        print("Failed to retrieve zip data.")
        exit()        

    with zipfile.ZipFile(zip_data) as zip_ref:
        changed_files = zip_ref.namelist()

        lookup_table = {metadata["xxHash"] : Hjson_Struct(metadata=metadata, seen=False)
                            for file_path in changed_files
                            if file_path.endswith('.hjson')
                            and (metadata := get_metadata_from_zip(zip_ref, file_path))}

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
        
        hjson_data_struct = lookup_table.get(xxhash_value)

        if hjson_data_struct is None:
            continue
        else:
            hjson_data_struct.seen = True
        
        copy = False
        for key in hjson_data_struct.metadata:
            if song_data.get(key, "") != str(hjson_data_struct.metadata[key]):
                copy = True
                print(f"They differ in {key}; {song_data.get(key, "")} vs {hjson_data_struct.metadata[key]}")

        if copy: 

            file_path = Path(song_path)

            new_payload = create_payload_from_dict(hjson_data=hjson_data_struct.metadata, song_path=song_path, filename=file_path.stem)
            engrave_payload(path=song_path, song_data=new_payload) ## side-effect

            song_obj = Song(song_path)
            process_new_tags(song_obj)

            format_tags(song_path, song_obj) ## side-effect

            if song_obj.filename != file_path.stem: ### have to figure out DF renaming
                renamed_path = file_path.parent / song_obj.filename
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

    seen_hjson_count = sum(1 for hjson_struct in lookup_table.values() if hjson_struct.seen is True) 
    print(f"Seen hjson files: {seen_hjson_count} < {(len(lookup_table) - 150)}") 

    if seen_hjson_count < (len(lookup_table) - 150):
        print("Missing files!")

    else:
        for hjson_struct in lookup_table.values():
            if hjson_struct.seen is False:
                pass
                print(f"Missing {hjson_struct.metadata.get("Title", "")}")