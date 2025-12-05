# YTVidDownloader

A lightweight YouTube video downloader with a simple GUI. Download videos in multiple qualities or extract audio-only files with optimal compression settings for minimal file sizes.

## Features

- **Multiple Quality Options**: 240p, 360p, 480p, 720p, 1080p, 1440p
- **Audio Extraction**: Extract audio-only in M4A format (128kbps AAC)
- **Space-Efficient Encoding**: H.264 (CRF 23) for video, AAC for audio
- **Real-Time Progress**: Live download progress bar with percentage
- **Simple GUI**: Clean tkinter interface, easy to use
- **Stop/Cancel**: Ability to stop downloads mid-progress
- **Customizable Save Location**: Choose where to save your downloads

## Screenshots

![YTVidDownloader Interface](screenshot.png)
*Simple and clean interface with real-time progress*

## Installation

### For End Users (Standalone)

Download the pre-built release from the [Releases](../../releases) page and follow the included README.

### For Developers

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jj-repository/YTVidDownloader.git
   cd YTVidDownloader
   ```

2. **Install system dependencies:**
   ```bash
   # Arch Linux
   sudo pacman -S ffmpeg yt-dlp

   # Ubuntu/Debian
   sudo apt install ffmpeg yt-dlp

   # Fedora
   sudo dnf install ffmpeg yt-dlp
   ```

3. **Set up Python environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Usage

### Running from Source

```bash
./run.sh
```

Or manually:
```bash
source venv/bin/activate
python downloader.py
```

### Using the Application

1. Paste a YouTube URL in the text field
2. Select your desired quality or choose audio-only
3. (Optional) Change the download location
4. Click **Download**
5. Watch the progress bar
6. Click **Stop** to cancel if needed

Downloads are saved to `~/Downloads` by default.

## Building Standalone Executable

To create a distributable executable:

```bash
source venv/bin/activate
pip install pyinstaller
pyinstaller --onefile --name YTVidDownloader --windowed downloader.py
```

The executable will be in the `dist/` folder.

## Technical Details

### File Formats & Compression

- **Video**: MP4 container with H.264 codec (CRF 23, medium preset)
- **Audio**: M4A format with AAC codec at 128kbps

These settings provide the best balance between file size and quality, keeping downloads as small as possible while maintaining good visual/audio fidelity.

### Dependencies

- **Python 3.6+**
- **yt-dlp**: YouTube download engine
- **ffmpeg**: Video/audio processing
- **tkinter**: GUI (usually included with Python)

## Requirements

- Linux (tested on Arch Linux)
- ~20 MB disk space
- Internet connection

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - The powerful YouTube download engine
- [FFmpeg](https://ffmpeg.org/) - Video/audio processing
