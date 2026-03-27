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
from typing import List, Tuple
import re
import os
import shutil
import sys
import time
import hashlib
from logger import get_logger

CHUNK_SIZE = 1024 * 1024  # 1 MiB for checksum read


def file_checksum(path: Path, algorithm: str = "sha256") -> str:
    """Compute hex digest of file contents (chunked read for large files)."""
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

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


def safe_move_file(src: Path, dest: Path) -> Tuple[bool, bool]:
    """
    Copy file to dest, verify copy by checksum, then remove source.
    On Windows, the source is often locked; we retry the delete a few times.
    Returns (copy_ok, source_removed). If copy_ok is True but source_removed is False,
    the file is at dest and the caller may inform the user to delete the original manually.
    """
    try:
        shutil.copy2(str(src), str(dest))
    except Exception as exc:
        logger.warning(f"safe_move_file: copy failed {src} -> {dest}: {exc}")
        return (False, False)

    if not dest.exists() or not dest.is_file():
        logger.warning(f"safe_move_file: copy completed but dest missing: {dest}")
        return (False, False)

    try:
        src_hash = file_checksum(src)
        dest_hash = file_checksum(dest)
        if src_hash != dest_hash:
            logger.warning(f"safe_move_file: checksum mismatch src={src_hash[:16]}... dest={dest_hash[:16]}...")
            try:
                dest.unlink()
            except OSError:
                pass
            return (False, False)
    except Exception as exc:
        logger.warning(f"safe_move_file: checksum verification failed: {exc}")
        try:
            dest.unlink()
        except OSError:
            pass
        return (False, False)

    # Retry delete on Windows when file may still be in use (e.g. player releasing handle)
    max_attempts = 15 if sys.platform == "win32" else 1
    delay = 0.4 if sys.platform == "win32" else 0
    for attempt in range(max_attempts):
        try:
            os.remove(str(src))
            return (True, True)
        except PermissionError as e:
            if attempt < max_attempts - 1:
                time.sleep(delay)
            else:
                logger.warning(f"safe_move_file: could not remove source (in use): {src}: {e}")
                return (True, False)
        except OSError as e:
            logger.warning(f"safe_move_file: could not remove source: {src}: {e}")
            return (True, False)
    return (True, False)


def safe_delete_file(path: Path) -> bool:
    """
    Remove a file, with retries on Windows when the file is in use (e.g. media player).
    Returns True if deleted, False if still locked after retries.
    """
    if not path.exists() or not path.is_file():
        return True
    max_attempts = 15 if sys.platform == "win32" else 1
    delay = 0.4 if sys.platform == "win32" else 0
    for attempt in range(max_attempts):
        try:
            os.remove(str(path))
            return True
        except PermissionError as e:
            if attempt < max_attempts - 1:
                time.sleep(delay)
            else:
                logger.warning(f"safe_delete_file: could not remove (in use): {path}: {e}")
                return False
        except OSError as e:
            logger.warning(f"safe_delete_file: could not remove: {path}: {e}")
            return False
    return False


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
