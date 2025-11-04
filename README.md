## 🎞 Slop Video Sorter

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



🎞 Slop Video Sorter

A tool for quickly browsing through massive amounts of video files.
Lets you instantly preview, keep the good ones, and delete the junk.
Perfect for sorting through AI-generated slop or hours of raw event footage like weddings.


### Features:
- quick saving playing file out the source folder
- buttons for quick navigation
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

### License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0).
See the [LICENSE](LICENSE) file for details.

