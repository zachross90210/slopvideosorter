"""
Slop Video Sorter: Utility functions for the video player application.

Copyright (C) 2025 zachross90210 <zachross90210@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from pathlib import Path
from typing import List
import re
import os
from logger import get_logger

logger = get_logger(__name__)


VIDEO_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".avi",
    ".mov",
    ".webm",
    ".mpg",
    ".mpeg",
    ".m4v",
    ".flv",
    ".wmv",
    ".m2ts",
    ".mts",
}

def is_video_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS


def unique_dest_path(dest_dir: Path, filename: str) -> Path:
    """Return dest_dir/filename, or stem_2.ext, stem_3.ext, ... if taken."""
    dest = dest_dir / filename
    if not dest.exists():
        return dest
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    n = 2
    while True:
        candidate = dest_dir / f"{stem}_{n}{suffix}"
        if not candidate.exists():
            return candidate
        n += 1


def natural_key(text: str) -> List[object]:
    # Split into digit and non-digit parts to get natural sorting
    return [int(s) if s.isdigit() else s.lower() for s in re.split(r"(\d+)", text)]


def derive_similarity_prefix(stem: str) -> str:
    """
    Try to extract a useful prefix for grouping similar files.
    Rules:
    - trim whitespace
    - drop trailing patterns like ' - copy', ' (1)', '_001', '-002', ' 1'
    - stop at the last separator before a trailing numeric run
    """
    name = stem.strip()
    # Remove common trailing copy markers
    name = re.sub(r"\s*\(copy\)$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s*-\s*copy$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s*copy\s*\d*$", "", name, flags=re.IGNORECASE)
    # Remove trailing (number)
    name = re.sub(r"\s*\(\d+\)$", "", name)
    # Remove trailing separators + digits: _001, -02,  3
    name = re.sub(r"[\s_\-]*\d+$", "", name)
    return name.strip()


def find_similar_files(reference_path: Path) -> List[Path]:
    directory = reference_path.parent
    stem = reference_path.stem
    prefix = derive_similarity_prefix(stem)
    if not prefix:
        prefix = stem

    candidates: List[Path] = []
    try:
        for child in directory.iterdir():
            if not is_video_file(child):
                continue
            if child == reference_path:
                continue
            child_stem = child.stem
            if child_stem.startswith(prefix):
                candidates.append(child)
    except Exception as exc:
        logger.debug(f"Error finding similar files in {directory}: {exc}")
        return []

    candidates.sort(key=lambda p: natural_key(p.name))
    return candidates


def get_saved_directory() -> Path:
    """Get the saved directory path from ~/.config/slopvideosorter/config, creating it with default if missing."""
    config_path = Path.home() / ".config" / "slopvideosorter" / "config"
    default_path = Path.home() / "Videos" / "_saved"
    
    try:
        if config_path.exists() and config_path.is_file():
            with open(config_path, "r", encoding="utf-8") as f:
                line = f.read().strip()
                if line:
                    p = Path(os.path.expanduser(line))
                    if p.is_absolute():
                        return p
                    # If relative, expand from home directory
                    return Path.home() / p
        
        # Config doesn't exist, create it with default path
        logger.info(f"Creating config file with default save directory: {default_path}")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(str(default_path))
        return default_path
    except Exception as exc:
        # Fallback to default on any error
        logger.warning(f"Error reading/creating config file, using default: {default_path}", exc_info=True)
        return default_path
