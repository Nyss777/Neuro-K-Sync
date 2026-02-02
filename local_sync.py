import argparse
import io
import logging
import os
import re
import sys
import zipfile
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path
from time import perf_counter
from typing import cast

import hjson
import requests
from DF_Customizer.file_manager import FileManager
from DF_formatter import apply_in_background, load_preset
from utils.CF_Program import Song, process_new_tags, set_tags_fast
from utils.create_hjsons import create_payload_from_dict
from utils.engraver import engrave_payload, get_all_mp3, get_raw_json
from utils.hash_mutagen import get_audio_hash


def format_tags(file_path: str, script_dir: Path, song_obj: Song, preset: dict[str, list[dict[str, str]]] | None) -> None:
    if not DF_format(file_path, script_dir, preset):
        set_tags_fast(song_path, song_obj, None, None)

def DF_format (file_path: str, script_dir: Path, preset: dict[str, list[dict[str, str]]] | None) -> bool:
    """
    Function for formatting a song with a DF preset
    """
    if preset is None:
        return False

    try:
        apply_in_background(file_path=file_path, fm=FileManager(), preset=preset)

    except Exception:
        logger.exception("Unable to format with preset!")
        return False

    else:
        return True

def setup_preset(script_dir: Path) -> dict[str, list[dict[str, str]]] | None:

    presets = get_all_json(script_dir)

    if not presets:
        return

    try :
        preset = load_preset(presets[0])

        if preset is None:
            return

    except Exception:
        logger.exception("Unable to load with preset!")
        return

    else:
        return preset

def get_all_json(p: Path) -> list[Path]: 
    """
    Function that gathers all JSON files from a directory.
    """
    return [(f) for f in p.rglob('*.json') if f.is_file()]

def get_remote_zip() -> io.BytesIO | None:
    url = "https://github.com/Nyss777/Neuro-Karaoke-Archive-Metadata/raw/main/zipped_metadata.zip"

    try:    

        response = requests.get(url)

        response.raise_for_status()

        if response.status_code == 200:
            # Wrap the bytes in a "BytesIO" object
            zip_in_memory = io.BytesIO(response.content)
            
            return zip_in_memory

    except requests.exceptions.HTTPError as err:
        status_code = err.response.status_code if err.response is not None else "Unknown"
        logger.error(f"Http Error: {status_code}")

    except requests.exceptions.ConnectionError:
        logger.exception("Error Connecting")

    except requests.exceptions.Timeout:
        logger.exception("Timeout Error")

    except requests.exceptions.RequestException:
        logger.exception("An Error Happened")

    return None

def get_metadata_from_zip(zip_ref: zipfile.ZipFile, hjson_path: str) -> dict[str, str|int|float] | None:
    # 1. Load the HJSON metadata
    try:
        with zip_ref.open(hjson_path, 'r') as f:
            content = f.read().decode('utf-8')
            metadata = cast(dict[str, str|int|float], hjson.loads(content))
        return metadata

    except Exception:
        logger.exception(f"Unable to process metadata for {os.path.basename(hjson_path)}!")
        return None

def get_songs_directory(path_config_file: Path, args: argparse.Namespace) -> Path | None:

    ### Priority list:
    # 1. args.path
    # 2. config
    # 3. window selection

    if args.path and (arg_path := Path(args.path)).is_dir():
        return arg_path

    elif path_config_file.exists():
        try:
            with open(path_config_file, 'r', encoding='utf-8') as h:
                config_content = h.read()
            if (config_path := Path(config_content)).is_dir():
                return config_path
        except PermissionError:
            logger.error("Permission Error. Unable to load path_config.txt")
    
    else:
        logger.debug("No path configuration found, loading selection window")
        selected = folder_selection_dialog()
        if selected is not None and (selected_path := Path(selected)).is_dir():
            return selected_path
            
    return None

def folder_selection_dialog() -> str | None:

    """Opens a file selection dialog and returns the selected file path."""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()

        folder_path = filedialog.askdirectory(
            title="Select the Neuro songs location",
            initialdir=os.getcwd()
        )

        root.destroy()

        if folder_path:
            logger.debug(f"Selected folder path: {folder_path}")
            return folder_path
        else:
            logger.info("No folder path selected")

    except ImportError:
        logger.critical("\nGUI selection unavailable (Tkinter not found).\n Please pass the path as an argument!")
        return None

def save_path(path_config_file: Path, directory: Path) -> None:
    try:
        if Path(path_config_file).exists():
            with open(path_config_file, 'r+', encoding='utf-8') as h:
                content = h.read()
                if Path(content) == directory:
                    return

        with open(path_config_file, 'w', encoding='utf-8') as h:
            h.write(str(directory))
    except PermissionError:
        logger.error("Permission Error. Unable to save path to disk.")

def setup_logger():

    logger = logging.getLogger()

    script_dir = Path(__file__).parent.absolute()

    log_path = script_dir / 'sync_log.txt'

    logger.setLevel(logging.DEBUG)

    file_formatter = logging.Formatter('[%(asctime)s]%(name)s-%(levelname)s:%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    shell_formatter = logging.Formatter('%(levelname)s: %(message)s')

    file_handler = RotatingFileHandler(log_path, maxBytes=5_242_880, backupCount=3, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(shell_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger

def setup_parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Neuro Karaoke Archive metadata synchronizer.") 
    parser.add_argument("--path", type=str, default='', help="Path to Archive")

    return parser.parse_args()

def get_raw(json: str, key: str) -> str: # test if this works

    pattern = f"\"{key}\":\"(.*?)\""

    match = re.search(pattern, json)

    if match is None:
        return ""
    else:
        return match.group(1)
 
@dataclass
class Hjson_Struct:
    metadata: dict[str, str | int | float]
    seen: bool

if __name__ == "__main__":

    start = perf_counter()

    setup_logger()

    if getattr(sys, 'frozen', False):
        script_dir = Path(sys.executable).parent
    else:
        script_dir = Path(__file__).parent.absolute()

    logger = logging.getLogger("Neuro K Archive Sync")

    logger.info("Run start")

    args = setup_parser()

    zip_data = get_remote_zip()

    if zip_data is None:
        logger.critical("Failed to retrieve zip data.")
        exit()        

    with zipfile.ZipFile(zip_data) as zip_ref:
        zipped_files = zip_ref.namelist()

        lookup_table = {metadata["xxHash"] : Hjson_Struct(metadata=metadata, seen=False)
                        for file_path in zipped_files
                        if file_path.endswith('.hjson')
                        and (metadata := get_metadata_from_zip(zip_ref, file_path))}

    path_config_file = script_dir / "path_config.txt"

    preset = setup_preset(script_dir)

    songs_directory_path = get_songs_directory(path_config_file, args)

    if songs_directory_path is None:
        logger.critical("Unable to retrieve path information, ending program")
        exit()

    save_path(path_config_file, songs_directory_path)

    song_files = get_all_mp3(songs_directory_path)
    if len(song_files) > 0:
        logger.info(f"Songs Found: {len(song_files)}")
    else:
        logger.critical("No song files found, please verify path")
        exit()

    end_setup = perf_counter()
    print(f"Time to setup: {round(end_setup-start, 2)} seconds")

    get_raw_time = 0
    hash_generating_time = 0

    changed = 0
    for song_path in song_files:
        get_raw_start = perf_counter()
        payload = get_raw_json(song_path)
        get_raw_time += (perf_counter() - get_raw_start)

        xxhash_value = get_raw(payload, "xxHash")

        if not xxhash_value:
            h_start = perf_counter()
            xxhash_value = get_audio_hash(song_path) # This takes a looooog time
            hash_generating_time += (perf_counter() - h_start)


        if not xxhash_value:
            logger.warning(f"Unable to get xxhash for {song_path}")
            continue
        
        hjson_data_struct = lookup_table.get(xxhash_value)

        if hjson_data_struct is None:
            continue
        else:
            hjson_data_struct.seen = True
        
        new_song_data = {k : v if isinstance(v, str) else f"{v}" for k, v in hjson_data_struct.metadata.items()}

        copy = False
        for key, value in new_song_data.items():
            if get_raw(payload, key) != value:
                copy = True
                changed += 1
                break


        if copy:

            file_path = Path(song_path)

            new_payload = create_payload_from_dict(hjson_data=hjson_data_struct.metadata, song_path=song_path, filename=file_path.stem)

            # engrave_payload(path=song_path, song_data=new_payload) ## side-effect

            song_obj = Song(song_path)
            process_new_tags(song_obj, song_data=new_song_data)

            # format_tags(song_path, script_dir, song_obj, preset) ## side-effect

            if song_obj.filename != file_path.stem:

                renamed_path = file_path.parent / song_obj.filename
                rename_counter = 1
                base_name = song_obj.filename

                while renamed_path.is_file():
                    renamed_path = file_path.parent / f"{base_name} ({rename_counter}){file_path.suffix}"
                    rename_counter += 1

                os.rename(src=song_path, dst=renamed_path) ## side-effect

    logger.debug(f"Time to process all files: {round(perf_counter()-end_setup, 2)} seconds")

    seen_hjson_count = sum(1 for hjson_struct in lookup_table.values() if hjson_struct.seen is True) 

    logger.info("Run End")
    if changed == 0:
        logger.info("No song was changed")
    else:
        logger.info(f"{changed} songs were updated")

    if seen_hjson_count < (len(lookup_table) - 150):
        logger.info("Many files are missing. If this is intentional, feel free to ignore this message.")

    elif all((struct.seen for struct in lookup_table.values())):
        logger.info("Your archive is fully up to date!")

    else:
        logger.info("Some files are missing, check the log file for details.")
        for hjson_struct in lookup_table.values():
            if hjson_struct.seen is False:
                logger.debug(f"Missing {hjson_struct.metadata.get("Track", "")} {hjson_struct.metadata.get("Title", "")}")
