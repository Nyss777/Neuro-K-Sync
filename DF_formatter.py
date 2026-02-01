import logging
from pathlib import Path
from typing import cast

import hjson
from file_manager import FileManager
from rule_manager import RuleManager
from song_utils import write_id3_tags

logger = logging.getLogger(__name__)

def load_preset(preset_path: Path) -> dict[str, list[dict[str, str]]] | None:

    try:
        with open(preset_path, 'r', encoding='utf-8') as handle:
            preset = cast(dict[str, list[dict[str, str]]], hjson.load(handle))

    except PermissionError:
        logger.error("Permission Error. Unable to load formatting preset")

    else:
        logger.debug(f"{preset_path.name} loaded")
        return preset

def apply_in_background(file_path: str, fm: FileManager, preset: dict[str, list[dict[str, str]]]) -> None:

    """Apply metadata changes in background thread."""
    
    success_count = 0

    try:
        metadata = fm.get_metadata(file_path=file_path)
        if not metadata.raw_data:
            logger.warning(f"No metadata: {Path(file_path).name}")
            return

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
            logger.exception(f"Failed to write: {Path(file_path).name}")

    except Exception:
        logger.exception(f"Error with {Path(file_path).name}")
