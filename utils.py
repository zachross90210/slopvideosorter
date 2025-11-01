from pathlib import Path
from typing import List
import re


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
    except Exception:
        return []

    candidates.sort(key=lambda p: natural_key(p.name))
    return candidates
