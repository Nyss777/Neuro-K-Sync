from pathlib import Path
from typing import cast

import hjson
from file_manager import FileManager
from rule_manager import RuleManager
from song_utils import write_id3_tags


def load_preset(preset_path: str) -> dict[str, list[dict[str, str]]]:
    with open(preset_path, 'r', encoding='utf-8') as handle:
        preset = cast(dict[str, list[dict[str, str]]], hjson.load(handle))
    
    print(f"{preset_path} loaded")
    return preset


def apply_in_background(file_path: str, fm: FileManager, preset: dict[str, list[dict[str, str]]]) -> None:
            """Apply metadata changes in background thread."""
            success_count = 0

            try:
                print(file_path)
                metadata = fm.get_metadata(file_path=file_path)
                print(metadata)
                if not metadata.raw_data:
                    raise Exception(f"No metadata: {Path(file_path).name}")

                new_title = RuleManager.apply_rules_list(
                    preset["title"],
                    metadata,
                )
                new_artist = RuleManager.apply_rules_list(
                    preset["artist"],
                    metadata,
                )
                new_album = RuleManager.apply_rules_list(
                    preset["album"],
                    metadata,
                )

                # write tags
                cover_bytes = None
                cover_mime = "image/jpeg"

                if write_id3_tags(
                    file_path,
                    title=new_title,
                    artist=new_artist,
                    album=new_album,
                    track=metadata.track,
                    disc=metadata.disc,
                    date=metadata.date,
                    cover_bytes=cover_bytes,
                    cover_mime=cover_mime,
                ):
                    success_count += 1
                else:
                    raise Exception(f"Failed to write: {Path(file_path).name}")

            except Exception as e:
                raise Exception(f"Error with {Path(file_path).name}: {e!s}")
