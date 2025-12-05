# How to Share YTVidDownloader with Your Friend

## Quick Answer

Send your friend the file: **`YTVidDownloader-Linux.tar.gz`** (14 MB)

That's it! They just need to extract it and run a simple setup script.

---

## Instructions for Your Friend

### Step 1: Extract the Archive
```bash
tar -xzf YTVidDownloader-Linux.tar.gz
cd YTVidDownloader-Linux/
```

Or just right-click the file and select "Extract Here" in your file manager.

### Step 2: Run Setup (checks dependencies)
```bash
./setup.sh
```

This will check if `ffmpeg` and `yt-dlp` are installed, and show the exact command to install them if needed.

### Step 3: Run the App
```bash
./YTVidDownloader
```

Or just double-click the `YTVidDownloader` file.

---

## What Your Friend Needs

### System Requirements:
- Linux (any distribution)
- About 20 MB of disk space
- Internet connection

### Dependencies (will be installed via setup.sh):
- **ffmpeg** - for video processing
- **yt-dlp** - for downloading videos

The setup script will detect the Linux distribution and show the exact command to install these.

---

## Quick Start Example

For Arch Linux users (like you), your friend would do:
```bash
# Extract
tar -xzf YTVidDownloader-Linux.tar.gz
cd YTVidDownloader-Linux/

# Install dependencies
sudo pacman -S ffmpeg yt-dlp

# Run the app
./YTVidDownloader
```

---

## What's Inside the Archive

- **YTVidDownloader** - The main executable (14 MB)
- **README.txt** - User documentation
- **setup.sh** - Dependency checker and installer guide

---

## Sharing the File

You can share `YTVidDownloader-Linux.tar.gz` via:
- Email attachment
- File sharing services (Google Drive, Dropbox, WeTransfer, etc.)
- USB drive
- Cloud storage

The file is about 14 MB, so it should be easy to share.

---

## Note

The app will:
- Save downloads to `~/Downloads` by default
- Let users choose video quality (240p to 1440p)
- Extract audio-only if needed
- Show real-time download progress
- Use space-efficient encoding (H.264/AAC)

Your friend doesn't need to know Python, set up virtual environments, or deal with any technical setup!
