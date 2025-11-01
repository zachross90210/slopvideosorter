## PyQt6 Video Player with Right-Side Playlist

Features:
- Right-side vertical playlist with blue selection highlight
- Double-click to play item
- Shift+Del permanently deletes selected items from disk and playlist
- Ctrl+Drag to reorder playlist items (only while Ctrl is held)
- Context menu: "Add similar files in folder" (adds files with similar names)

### Install (Linux)

1) System multimedia backends (GStreamer):

```bash
sudo apt update
sudo apt install -y \
  gstreamer1.0-tools \
  gstreamer1.0-libav \
  gstreamer1.0-plugins-base \
  gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad \
  gstreamer1.0-plugins-ugly
```

2) Python deps (use a venv if you want):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

### Run

```bash
python3 main.py
```

### Usage
- Open files: button or Ctrl+O
- Play/Pause: Space
- Double-click an item to play
- Select multiple items with Ctrl/Shift as usual (blue highlight)
- Delete selected from disk: Shift+Delete
- Reorder: Hold Ctrl, then drag items up/down
- Right-click playlist → "Add similar files in folder"

Notes:
- "Similar files" is determined by common filename prefix (e.g., trimming trailing numbers or copy marks) and matching video extensions.
- Shift+Delete removes files permanently (no trash). Use with care.

