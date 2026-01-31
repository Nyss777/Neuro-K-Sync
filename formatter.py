from pathlib import Path
from typing import cast

import hjson
from engraver import get_all_mp3
from file_manager import FileManager
from rule_manager import RuleManager
from song_utils import write_id3_tags


def load_preset() -> dict[str, list[dict[str, str]]]:
    with open("TuruuMGL.json", 'r', encoding='utf-8') as handle:
        preset = cast(dict[str, list[dict[str, str]]], hjson.load(handle))
    return preset


def apply_in_background(paths: list[str], fm: FileManager, preset: dict[str, list[dict[str, str]]]) -> None:
            """Apply metadata changes in background thread."""
            success_count = 0
            errors: list[str] = []

            for p in paths:

                try:
                    print(p)
                    metadata = fm.get_metadata(file_path=p)
                    print(metadata)
                    if not metadata.raw_data:
                        errors.append(f"No metadata: {Path(p).name}")
                        continue

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
                        p,
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
                        errors.append(f"Failed to write: {Path(p).name}")

                except Exception as e:
                    errors.append(f"Error with {Path(p).name}: {e!s}")
            print(errors)

if __name__ == "__main__":
    file_m = FileManager()
    preset = load_preset()
    files_location = r"C:\Users\Nyss\Downloads\testt\testlet"
    paths: list[str] = get_all_mp3(files_location)
    print(len(paths))
    apply_in_background(paths=paths, fm=file_m, preset=preset)