#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import subprocess
import threading
import re
import logging
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw, ImageFont
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, parse_qs

# Configure logging
log_dir = Path.home() / ".ytviddownloader"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "ytviddownloader.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
PREVIEW_WIDTH = 240
PREVIEW_HEIGHT = 135
SLIDER_LENGTH = 400
PREVIEW_DEBOUNCE_MS = 500
PROCESS_TERMINATE_TIMEOUT = 3
TEMP_DIR_MAX_AGE = 3600  # 1 hour
DOWNLOAD_TIMEOUT = 1800  # 30 minutes max for any download
DOWNLOAD_PROGRESS_TIMEOUT = 300  # 5 minutes without progress = stalled
PREVIEW_CACHE_SIZE = 20  # Cache up to 20 preview frames
MAX_WORKER_THREADS = 3  # Thread pool size for background tasks
MAX_RETRY_ATTEMPTS = 3  # Retry network operations up to 3 times
RETRY_DELAY = 2  # Seconds between retry attempts

class YouTubeDownloader:
    def __init__(self, root):
        logger.info("Initializing YTVidDownloader")
        self.root = root
        self.root.title("YTVidDownloader")
        self.root.geometry("1100x1200")
        self.root.resizable(True, True)
        self.root.minsize(750, 600)

        self.download_path = str(Path.home() / "Downloads")
        self.current_process = None
        self.is_downloading = False
        self.video_duration = 0
        self.is_fetching_duration = False
        self.last_progress_time = None
        self.download_start_time = None
        self.timeout_monitor_thread = None

        # Frame preview variables
        self.start_preview_image = None
        self.end_preview_image = None
        self.temp_dir = None
        self.current_video_url = None
        self.preview_update_timer = None
        self.last_preview_update = 0
        self.preview_thread_running = False  # Track if preview thread is active
        self.preview_cache = {}  # Cache for preview frames {timestamp: file_path}
        self.cache_access_order = []  # Track access order for LRU eviction

        # Initialize temp directory with cleanup on exit
        self._init_temp_directory()

        # Find yt-dlp executable
        self.ytdlp_path = self.find_ytdlp()

        # Check dependencies once at startup
        self.dependencies_ok = self.check_dependencies()
        if not self.dependencies_ok:
            logger.warning("Dependencies check failed at startup")

        # Thread pool for background tasks
        self.thread_pool = ThreadPoolExecutor(max_workers=MAX_WORKER_THREADS, thread_name_prefix="ytdl_worker")

        self.setup_ui()

        # Bind cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def find_ytdlp(self):
        """Find yt-dlp in various locations"""
        # Check if running as PyInstaller bundle
        if getattr(sys, 'frozen', False):
            bundle_dir = Path(sys.executable).parent
            # Check in same directory as executable
            ytdlp_local = bundle_dir / "yt-dlp"
            if ytdlp_local.exists():
                return str(ytdlp_local)
        else:
            # Running from source, check venv
            venv_path = Path(sys.executable).parent
            ytdlp_venv = venv_path / "yt-dlp"
            if ytdlp_venv.exists():
                return str(ytdlp_venv)

        # Fall back to system PATH
        return "yt-dlp"

    def retry_network_operation(self, operation, operation_name, *args, **kwargs):
        """Retry a network operation with exponential backoff"""
        for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
            try:
                return operation(*args, **kwargs)
            except subprocess.TimeoutExpired as e:
                if attempt == MAX_RETRY_ATTEMPTS:
                    logger.error(f"{operation_name} failed after {MAX_RETRY_ATTEMPTS} attempts: timeout")
                    raise
                logger.warning(f"{operation_name} timeout (attempt {attempt}/{MAX_RETRY_ATTEMPTS}), retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY * attempt)  # Exponential backoff
            except subprocess.CalledProcessError as e:
                if attempt == MAX_RETRY_ATTEMPTS:
                    logger.error(f"{operation_name} failed after {MAX_RETRY_ATTEMPTS} attempts: {e}")
                    raise
                logger.warning(f"{operation_name} failed (attempt {attempt}/{MAX_RETRY_ATTEMPTS}), retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY * attempt)
            except Exception as e:
                # Don't retry on unexpected errors
                logger.error(f"{operation_name} failed with unexpected error: {e}")
                raise

    def validate_youtube_url(self, url):
        """Validate if URL is a valid YouTube URL"""
        if not url:
            return False, "URL is empty"

        try:
            parsed = urlparse(url)

            # Check for valid YouTube domains
            valid_domains = [
                'youtube.com', 'www.youtube.com', 'm.youtube.com',
                'youtu.be', 'www.youtu.be'
            ]

            if parsed.netloc not in valid_domains:
                return False, "Not a YouTube URL. Please enter a valid YouTube link."

            # For youtu.be short links
            if 'youtu.be' in parsed.netloc:
                if not parsed.path or parsed.path == '/':
                    return False, "Invalid YouTube short URL"
                return True, "Valid YouTube URL"

            # For youtube.com links
            if 'youtube.com' in parsed.netloc:
                # Check for /watch?v= format
                if '/watch' in parsed.path:
                    query_params = parse_qs(parsed.query)
                    if 'v' not in query_params:
                        return False, "Missing video ID in URL"
                    return True, "Valid YouTube URL"

                # Check for /shorts/ format
                elif '/shorts/' in parsed.path:
                    return True, "Valid YouTube Shorts URL"

                # Check for /embed/ format
                elif '/embed/' in parsed.path:
                    return True, "Valid YouTube embed URL"

                # Check for /v/ format (old style)
                elif '/v/' in parsed.path:
                    return True, "Valid YouTube URL"

                else:
                    return False, "Unrecognized YouTube URL format"

            return False, "Invalid URL format"

        except Exception as e:
            logger.error(f"URL validation error: {e}")
            return False, f"Invalid URL format: {str(e)}"

    def _init_temp_directory(self):
        """Initialize temp directory and clean up orphaned ones from previous crashes"""
        import shutil
        import glob

        # Clean up old orphaned temp directories
        temp_base = tempfile.gettempdir()
        old_dirs = glob.glob(os.path.join(temp_base, "ytdl_preview_*"))
        for old_dir in old_dirs:
            try:
                # Only remove if older than TEMP_DIR_MAX_AGE (to avoid conflicts with other instances)
                dir_age = time.time() - os.path.getmtime(old_dir)
                if dir_age > TEMP_DIR_MAX_AGE:
                    shutil.rmtree(old_dir, ignore_errors=True)
            except Exception:
                pass

        # Create new temp directory
        self.temp_dir = tempfile.mkdtemp(prefix="ytdl_preview_")

    def setup_ui(self):
        # Configure root grid to expand
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Create canvas with scrollbar for scrollable content
        canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        # Bind mousewheel to canvas only (not globally to avoid leaks)
        canvas.bind("<MouseWheel>", _on_mousewheel)

        # Store canvas reference for cleanup
        self.canvas = canvas

        main_frame = ttk.Frame(scrollable_frame, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(main_frame, text="YouTube URL:", font=('Arial', 12)).grid(row=0, column=0, sticky=tk.W, pady=(0, 10))

        self.url_entry = ttk.Entry(main_frame, width=60)
        self.url_entry.grid(row=1, column=0, columnspan=2, pady=(0, 20))

        # Video Quality section
        ttk.Label(main_frame, text="Video Quality:", font=('Arial', 11, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=(10, 5))

        self.quality_var = tk.StringVar(value="480")

        ttk.Radiobutton(main_frame, text="1440p (2560x1440)", variable=self.quality_var, value="1440").grid(row=3, column=0, sticky=tk.W, padx=(20, 0))
        ttk.Radiobutton(main_frame, text="1080p (1920x1080)", variable=self.quality_var, value="1080").grid(row=4, column=0, sticky=tk.W, padx=(20, 0))
        ttk.Radiobutton(main_frame, text="720p (1280x720)", variable=self.quality_var, value="720").grid(row=5, column=0, sticky=tk.W, padx=(20, 0))
        ttk.Radiobutton(main_frame, text="480p (854x480)", variable=self.quality_var, value="480").grid(row=6, column=0, sticky=tk.W, padx=(20, 0))
        ttk.Radiobutton(main_frame, text="360p (640x360)", variable=self.quality_var, value="360").grid(row=7, column=0, sticky=tk.W, padx=(20, 0))
        ttk.Radiobutton(main_frame, text="240p (426x240)", variable=self.quality_var, value="240").grid(row=8, column=0, sticky=tk.W, padx=(20, 0))
        ttk.Radiobutton(main_frame, text="None (Audio only)", variable=self.quality_var, value="none").grid(row=9, column=0, sticky=tk.W, padx=(20, 0))

        ttk.Separator(main_frame, orient='horizontal').grid(row=10, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15)

        # Trimming section
        ttk.Label(main_frame, text="Trim Video:", font=('Arial', 11, 'bold')).grid(row=11, column=0, sticky=tk.W, pady=(0, 3))

        self.trim_enabled_var = tk.BooleanVar()
        trim_check = ttk.Checkbutton(main_frame, text="Enable video trimming", variable=self.trim_enabled_var,
                                     command=self.toggle_trim).grid(row=12, column=0, sticky=tk.W, padx=(20, 0))

        self.fetch_duration_btn = ttk.Button(main_frame, text="Fetch Video Duration", command=self.fetch_duration_clicked, state='disabled')
        self.fetch_duration_btn.grid(row=13, column=0, sticky=tk.W, padx=(20, 0), pady=(3, 5))

        self.duration_label = ttk.Label(main_frame, text="Total Duration: --:--:--", foreground="gray")
        self.duration_label.grid(row=14, column=0, sticky=tk.W, padx=(20, 0))

        # Video info label
        self.video_info_label = ttk.Label(main_frame, text="", foreground="blue", wraplength=500, justify=tk.LEFT)
        self.video_info_label.grid(row=15, column=0, sticky=tk.W, padx=(20, 0), pady=(2, 0))

        # Preview frame to hold both previews side by side
        preview_container = ttk.Frame(main_frame)
        preview_container.grid(row=16, column=0, sticky=tk.W, padx=(40, 0), pady=(10, 5))

        # Start time preview
        start_preview_frame = ttk.Frame(preview_container)
        start_preview_frame.grid(row=0, column=0, padx=(0, 20))

        ttk.Label(start_preview_frame, text="Start Time:", font=('Arial', 9)).pack()
        self.start_preview_label = tk.Label(start_preview_frame, bg='gray20', fg='white', relief='sunken')
        self.start_preview_label.pack(pady=(5, 0))

        # Create placeholder images
        self.placeholder_image = self.create_placeholder_image(PREVIEW_WIDTH, PREVIEW_HEIGHT, "Preview")
        self.loading_image = self.create_placeholder_image(PREVIEW_WIDTH, PREVIEW_HEIGHT, "Loading...")
        self.start_preview_label.config(image=self.placeholder_image)

        # End time preview
        end_preview_frame = ttk.Frame(preview_container)
        end_preview_frame.grid(row=0, column=1)

        ttk.Label(end_preview_frame, text="End Time:", font=('Arial', 9)).pack()
        self.end_preview_label = tk.Label(end_preview_frame, bg='gray20', fg='white', relief='sunken')
        self.end_preview_label.pack(pady=(5, 0))
        self.end_preview_label.config(image=self.placeholder_image)

        # Start time slider and entry
        start_control_frame = ttk.Frame(main_frame)
        start_control_frame.grid(row=17, column=0, sticky=tk.W, padx=(40, 0), pady=(2, 2))

        self.start_time_var = tk.DoubleVar(value=0)
        self.start_slider = ttk.Scale(start_control_frame, from_=0, to=100, variable=self.start_time_var,
                                      orient='horizontal', length=SLIDER_LENGTH, command=self.on_slider_change, state='disabled')
        self.start_slider.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(start_control_frame, text="Start:", font=('Arial', 9)).pack(side=tk.LEFT, padx=(0, 5))
        self.start_time_entry = ttk.Entry(start_control_frame, width=10, state='disabled')
        self.start_time_entry.pack(side=tk.LEFT)
        self.start_time_entry.insert(0, "00:00:00")
        self.start_time_entry.bind('<Return>', self.on_start_entry_change)
        self.start_time_entry.bind('<FocusOut>', self.on_start_entry_change)

        # End time slider and entry
        end_control_frame = ttk.Frame(main_frame)
        end_control_frame.grid(row=18, column=0, sticky=tk.W, padx=(40, 0), pady=(2, 2))

        self.end_time_var = tk.DoubleVar(value=100)
        self.end_slider = ttk.Scale(end_control_frame, from_=0, to=100, variable=self.end_time_var,
                                    orient='horizontal', length=SLIDER_LENGTH, command=self.on_slider_change, state='disabled')
        self.end_slider.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(end_control_frame, text="End:", font=('Arial', 9)).pack(side=tk.LEFT, padx=(0, 5))
        self.end_time_entry = ttk.Entry(end_control_frame, width=10, state='disabled')
        self.end_time_entry.pack(side=tk.LEFT)
        self.end_time_entry.insert(0, "00:00:00")
        self.end_time_entry.bind('<Return>', self.on_end_entry_change)
        self.end_time_entry.bind('<FocusOut>', self.on_end_entry_change)

        # Trim duration display
        self.trim_duration_label = ttk.Label(main_frame, text="Selected Duration: 00:00:00", foreground="green", font=('Arial', 9, 'bold'))
        self.trim_duration_label.grid(row=19, column=0, sticky=tk.W, padx=(40, 0), pady=(3, 0))

        ttk.Separator(main_frame, orient='horizontal').grid(row=20, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15)

        path_frame = ttk.Frame(main_frame)
        path_frame.grid(row=21, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(path_frame, text="Save to:").pack(side=tk.LEFT)
        self.path_label = ttk.Label(path_frame, text=self.download_path, foreground="blue")
        self.path_label.pack(side=tk.LEFT, padx=(10, 10))
        ttk.Button(path_frame, text="Change", command=self.change_path).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(path_frame, text="Open Folder", command=self.open_download_folder).pack(side=tk.LEFT)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=22, column=0, columnspan=2, pady=(0, 10))

        self.download_btn = ttk.Button(button_frame, text="Download", command=self.start_download)
        self.download_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_btn = ttk.Button(button_frame, text="Stop", command=self.stop_download, state='disabled')
        self.stop_btn.pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(main_frame, mode='determinate', length=560, maximum=100)
        self.progress.grid(row=23, column=0, columnspan=2)

        self.progress_label = ttk.Label(main_frame, text="0%", foreground="blue")
        self.progress_label.grid(row=24, column=0, columnspan=2, pady=(5, 0))

        self.status_label = ttk.Label(main_frame, text="Ready", foreground="green")
        self.status_label.grid(row=25, column=0, columnspan=2, pady=(10, 0))

    def create_placeholder_image(self, width, height, text):
        """Create a placeholder image with text"""
        img = Image.new('RGB', (width, height), color='#2d2d2d')
        draw = ImageDraw.Draw(img)

        # Draw text in center - use default font for cross-platform compatibility
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None

        # Get text bounding box to center it
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        position = ((width - text_width) // 2, (height - text_height) // 2)
        draw.text(position, text, fill='white', font=font)

        return ImageTk.PhotoImage(img)

    def seconds_to_hms(self, seconds):
        """Convert seconds to HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def toggle_trim(self):
        """Enable or disable trimming controls"""
        enabled = self.trim_enabled_var.get()
        if enabled:
            self.fetch_duration_btn.config(state='normal')
            if self.video_duration > 0:
                self.start_slider.config(state='normal')
                self.end_slider.config(state='normal')
                self.start_time_entry.config(state='normal')
                self.end_time_entry.config(state='normal')
        else:
            self.fetch_duration_btn.config(state='disabled')
            self.start_slider.config(state='disabled')
            self.end_slider.config(state='disabled')
            self.start_time_entry.config(state='disabled')
            self.end_time_entry.config(state='disabled')

    def fetch_duration_clicked(self):
        """Handler for fetch duration button"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL first")
            return

        # Validate URL
        is_valid, message = self.validate_youtube_url(url)
        if not is_valid:
            messagebox.showerror("Invalid URL", message)
            logger.warning(f"Invalid URL rejected: {url}")
            return

        if self.is_fetching_duration or self.is_downloading:
            return

        # Save the URL for preview extraction and clear cache
        if self.current_video_url != url:
            self.current_video_url = url
            self._clear_preview_cache()
        else:
            self.current_video_url = url

        self.is_fetching_duration = True
        self.fetch_duration_btn.config(state='disabled')
        self.update_status("Fetching video duration...", "blue")

        # Submit to thread pool
        self.thread_pool.submit(self.fetch_video_duration, url)

    def fetch_video_duration(self, url):
        """Fetch video duration and info from URL"""
        try:
            # Fetch duration
            def _fetch_duration():
                cmd = [self.ytdlp_path, '--get-duration', url]
                return subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            result = self.retry_network_operation(_fetch_duration, "Fetch duration")

            # Fetch title in parallel
            def _fetch_title():
                cmd = [self.ytdlp_path, '--get-title', url]
                return subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            title_result = self.retry_network_operation(_fetch_title, "Fetch title")

            if result.returncode == 0:
                duration_str = result.stdout.strip()
                # Parse duration (format can be MM:SS or HH:MM:SS)
                parts = duration_str.split(':')
                if len(parts) == 2:  # MM:SS
                    self.video_duration = int(parts[0]) * 60 + int(parts[1])
                elif len(parts) == 3:  # HH:MM:SS
                    self.video_duration = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                else:
                    raise ValueError("Invalid duration format")

                # Update UI
                self.duration_label.config(
                    text=f"Total Duration: {self.seconds_to_hms(self.video_duration)}",
                    foreground="green"
                )

                # Update sliders
                self.start_slider.config(from_=0, to=self.video_duration, state='normal')
                self.end_slider.config(from_=0, to=self.video_duration, state='normal')
                self.start_time_var.set(0)
                self.end_time_var.set(self.video_duration)

                # Update entry fields
                self.start_time_entry.config(state='normal')
                self.end_time_entry.config(state='normal')
                self.start_time_entry.delete(0, tk.END)
                self.start_time_entry.insert(0, self.seconds_to_hms(0))
                self.end_time_entry.delete(0, tk.END)
                self.end_time_entry.insert(0, self.seconds_to_hms(self.video_duration))

                # Update duration label
                self.trim_duration_label.config(text=f"Selected Duration: {self.seconds_to_hms(self.video_duration)}")

                # Display video title if available
                if title_result and title_result.returncode == 0:
                    video_title = title_result.stdout.strip()
                    self.video_info_label.config(text=f"Title: {video_title}")
                    logger.info(f"Video title: {video_title}")

                self.update_status("Duration fetched successfully", "green")

                # Trigger initial preview update
                self.root.after(100, self.update_previews)
                logger.info(f"Successfully fetched video duration: {self.video_duration}s")
            else:
                raise Exception(f"yt-dlp returned error: {result.stderr}")

        except subprocess.TimeoutExpired:
            error_msg = "Request timed out. Please check your internet connection."
            messagebox.showerror("Error", error_msg)
            self.update_status("Duration fetch timed out", "red")
            logger.error("Timeout fetching video duration")
        except ValueError as e:
            error_msg = f"Invalid duration format received: {str(e)}"
            messagebox.showerror("Error", error_msg)
            self.update_status("Invalid duration format", "red")
            logger.error(f"Duration parsing error: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch video duration:\n{str(e)}")
            self.update_status("Failed to fetch duration", "red")
            logger.exception(f"Unexpected error fetching duration: {e}")

        finally:
            self.is_fetching_duration = False
            if self.trim_enabled_var.get():
                self.fetch_duration_btn.config(state='normal')

    def on_slider_change(self, event=None):
        """Handle slider changes"""
        start_time = int(self.start_time_var.get())
        end_time = int(self.end_time_var.get())

        # Ensure start is before end
        if start_time >= end_time:
            if event:  # Only adjust if this was a user interaction
                # Determine which slider was moved and adjust the other
                if abs(self.start_slider.get() - start_time) < 0.1:  # Start slider was moved
                    end_time = min(start_time + 1, self.video_duration)
                    self.end_time_var.set(end_time)
                else:  # End slider was moved
                    start_time = max(end_time - 1, 0)
                    self.start_time_var.set(start_time)

        # Update entry fields
        self.start_time_entry.delete(0, tk.END)
        self.start_time_entry.insert(0, self.seconds_to_hms(start_time))
        self.end_time_entry.delete(0, tk.END)
        self.end_time_entry.insert(0, self.seconds_to_hms(end_time))

        # Update selected duration
        selected_duration = end_time - start_time
        self.trim_duration_label.config(text=f"Selected Duration: {self.seconds_to_hms(selected_duration)}")

        # Schedule preview update with debouncing
        self.schedule_preview_update()

    def hms_to_seconds(self, hms_str):
        """Convert HH:MM:SS format to seconds"""
        try:
            parts = hms_str.strip().split(':')
            if len(parts) != 3:
                return None
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        except (ValueError, AttributeError):
            return None

    def on_start_entry_change(self, event=None):
        """Handle changes to start time entry field"""
        value_str = self.start_time_entry.get()
        seconds = self.hms_to_seconds(value_str)

        if seconds is not None and 0 <= seconds <= self.video_duration:
            # Valid input, update the slider
            self.start_time_var.set(seconds)
            # on_slider_change will be called automatically via the variable trace
            # But we need to trigger it manually since we're setting the variable directly
            self.on_slider_change()
        else:
            # Invalid input, restore the current value
            current_time = int(self.start_time_var.get())
            self.start_time_entry.delete(0, tk.END)
            self.start_time_entry.insert(0, self.seconds_to_hms(current_time))

    def on_end_entry_change(self, event=None):
        """Handle changes to end time entry field"""
        value_str = self.end_time_entry.get()
        seconds = self.hms_to_seconds(value_str)

        if seconds is not None and 0 <= seconds <= self.video_duration:
            # Valid input, update the slider
            self.end_time_var.set(seconds)
            # Trigger slider change handler
            self.on_slider_change()
        else:
            # Invalid input, restore the current value
            current_time = int(self.end_time_var.get())
            self.end_time_entry.delete(0, tk.END)
            self.end_time_entry.insert(0, self.seconds_to_hms(current_time))

    def schedule_preview_update(self):
        """Schedule preview update with debouncing to avoid excessive calls"""
        # Cancel any pending update
        if self.preview_update_timer:
            self.root.after_cancel(self.preview_update_timer)

        # Schedule new update after debounce delay
        self.preview_update_timer = self.root.after(PREVIEW_DEBOUNCE_MS, self.update_previews)

    def _clear_preview_cache(self):
        """Clear the preview frame cache"""
        logger.info("Clearing preview cache")
        self.preview_cache.clear()
        self.cache_access_order.clear()

    def _cache_preview_frame(self, timestamp, file_path):
        """Add a frame to the cache with LRU eviction"""
        # Remove oldest if cache is full
        if len(self.preview_cache) >= PREVIEW_CACHE_SIZE:
            if self.cache_access_order:
                oldest = self.cache_access_order.pop(0)
                if oldest in self.preview_cache:
                    old_path = self.preview_cache.pop(oldest)
                    # Optionally delete the old cached file
                    try:
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    except Exception:
                        pass

        # Add to cache
        self.preview_cache[timestamp] = file_path
        if timestamp in self.cache_access_order:
            self.cache_access_order.remove(timestamp)
        self.cache_access_order.append(timestamp)

    def _get_cached_frame(self, timestamp):
        """Get a cached frame if available"""
        if timestamp in self.preview_cache:
            # Update access order (move to end as most recently used)
            if timestamp in self.cache_access_order:
                self.cache_access_order.remove(timestamp)
            self.cache_access_order.append(timestamp)
            return self.preview_cache[timestamp]
        return None

    def extract_frame(self, timestamp):
        """Extract a single frame at the given timestamp"""
        if not self.current_video_url:
            return None

        # Check cache first
        cached = self._get_cached_frame(timestamp)
        if cached and os.path.exists(cached):
            logger.debug(f"Using cached frame for timestamp {timestamp}s")
            return cached

        try:
            # Create unique temp file for this frame
            temp_file = os.path.join(self.temp_dir, f"frame_{timestamp}.jpg")

            # Get the actual video stream URL using yt-dlp with retry
            def _get_stream_url():
                get_url_cmd = [
                    self.ytdlp_path,
                    '-f', 'bestvideo[height<=480]/best[height<=480]',
                    '-g',
                    self.current_video_url
                ]
                return subprocess.run(get_url_cmd, capture_output=True, text=True, timeout=15, check=True)

            result = self.retry_network_operation(_get_stream_url, f"Get stream URL for frame at {timestamp}s")
            video_url = result.stdout.strip().split('\n')[0]

            # Now extract frame from the actual stream with retry
            def _extract_frame():
                cmd = [
                    'ffmpeg',
                    '-ss', str(timestamp),
                    '-i', video_url,
                    '-vframes', '1',
                    '-q:v', '2',
                    '-y',
                    temp_file
                ]
                return subprocess.run(cmd, capture_output=True, timeout=15, check=True)

            self.retry_network_operation(_extract_frame, f"Extract frame at {timestamp}s")

            if os.path.exists(temp_file):
                # Cache the extracted frame
                self._cache_preview_frame(timestamp, temp_file)
                return temp_file

        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout while extracting frame at {timestamp}s")
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error extracting frame at {timestamp}s: {e}")
        except Exception as e:
            logger.error(f"Unexpected error extracting frame at {timestamp}s: {e}")

        return None

    def update_previews(self):
        """Update both preview images"""
        if not self.current_video_url or self.video_duration == 0:
            return

        # Prevent spawning multiple preview threads
        if self.preview_thread_running:
            return

        start_time = int(self.start_time_var.get())
        end_time = int(self.end_time_var.get())

        # Show loading indicators
        self.start_preview_label.config(image=self.loading_image)
        self.end_preview_label.config(image=self.loading_image)

        # Submit to thread pool instead of creating new thread
        self.thread_pool.submit(self._update_previews_thread, start_time, end_time)

    def _update_previews_thread(self, start_time, end_time):
        """Background thread to extract and update preview frames"""
        try:
            self.preview_thread_running = True
            logger.info(f"Extracting preview frames at {start_time}s and {end_time}s")

            # Extract start frame
            start_frame_path = self.extract_frame(start_time)
            if start_frame_path:
                self._update_preview_image(start_frame_path, 'start')
            else:
                # Show error placeholder if extraction failed
                error_img = self.create_placeholder_image(PREVIEW_WIDTH, PREVIEW_HEIGHT, "Error")
                self.root.after(0, lambda: self._set_start_preview(ImageTk.PhotoImage(error_img)))

            # Extract end frame
            end_frame_path = self.extract_frame(end_time)
            if end_frame_path:
                self._update_preview_image(end_frame_path, 'end')
            else:
                # Show error placeholder if extraction failed
                error_img = self.create_placeholder_image(PREVIEW_WIDTH, PREVIEW_HEIGHT, "Error")
                self.root.after(0, lambda: self._set_end_preview(ImageTk.PhotoImage(error_img)))
        finally:
            self.preview_thread_running = False

    def _update_preview_image(self, image_path, position):
        """Update preview image in UI (must be called from main thread or scheduled)"""
        try:
            # Load and resize image
            img = Image.open(image_path)
            img.thumbnail((PREVIEW_WIDTH, PREVIEW_HEIGHT), Image.Resampling.LANCZOS)

            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)

            # Schedule UI update on main thread
            if position == 'start':
                self.root.after(0, lambda: self._set_start_preview(photo))
            else:
                self.root.after(0, lambda: self._set_end_preview(photo))

        except Exception as e:
            logger.error(f"Error updating preview image for {position}: {e}")

    def _set_start_preview(self, photo):
        """Set start preview image (called on main thread)"""
        self.start_preview_image = photo  # Keep reference to avoid garbage collection
        self.start_preview_label.config(image=photo, text='')

    def _set_end_preview(self, photo):
        """Set end preview image (called on main thread)"""
        self.end_preview_image = photo  # Keep reference to avoid garbage collection
        self.end_preview_label.config(image=photo, text='')

    def change_path(self):
        """Change download path with validation"""
        path = filedialog.askdirectory(initialdir=self.download_path)
        if path:
            # Validate that path exists and is writable
            if not os.path.exists(path):
                messagebox.showerror("Error", f"Path does not exist: {path}")
                return

            if not os.path.isdir(path):
                messagebox.showerror("Error", f"Path is not a directory: {path}")
                return

            # Test write permissions
            test_file = os.path.join(path, ".ytdl_write_test")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
            except (IOError, OSError) as e:
                messagebox.showerror("Error", f"Path is not writable:\n{path}\n\n{str(e)}")
                return

            self.download_path = path
            self.path_label.config(text=path)

    def open_download_folder(self):
        """Open the download folder in the system file manager"""
        try:
            if sys.platform == 'win32':
                os.startfile(self.download_path)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', self.download_path])
            else:
                subprocess.Popen(['xdg-open', self.download_path])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder:\n{str(e)}")

    def check_dependencies(self):
        """Check if yt-dlp and ffmpeg are available"""
        try:
            # Check yt-dlp
            result = subprocess.run([self.ytdlp_path, '--version'],
                                  capture_output=True, check=True, timeout=5)
            logger.info(f"yt-dlp version: {result.stdout.decode().strip()}")

            # Check ffmpeg
            result = subprocess.run(['ffmpeg', '-version'],
                                  capture_output=True, check=True, timeout=5)
            logger.info("ffmpeg is available")

            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.error(f"Dependency check failed: {e}")
            return False

    def start_download(self):
        url = self.url_entry.get().strip()

        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return

        # Validate URL
        is_valid, message = self.validate_youtube_url(url)
        if not is_valid:
            messagebox.showerror("Invalid URL", message)
            logger.warning(f"Invalid URL rejected for download: {url}")
            return

        if not self.dependencies_ok:
            messagebox.showerror("Error", "yt-dlp or ffmpeg is not installed.\n\nInstall with:\npip install yt-dlp\n\nand install ffmpeg from your package manager")
            return

        logger.info(f"Starting download for URL: {url}")

        self.is_downloading = True
        self.download_start_time = time.time()
        self.last_progress_time = time.time()
        self.download_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.progress['value'] = 0
        self.progress_label.config(text="0%")

        # Submit download and timeout monitor to thread pool
        self.thread_pool.submit(self.download, url)
        self.thread_pool.submit(self._monitor_download_timeout)

    def _monitor_download_timeout(self):
        """Monitor download for timeouts (absolute and progress-based)"""
        while self.is_downloading:
            time.sleep(10)  # Check every 10 seconds

            if not self.is_downloading:
                break

            current_time = time.time()

            # Check absolute timeout
            if self.download_start_time:
                elapsed = current_time - self.download_start_time
                if elapsed > DOWNLOAD_TIMEOUT:
                    logger.error(f"Download exceeded absolute timeout ({DOWNLOAD_TIMEOUT}s)")
                    self.root.after(0, lambda: self._timeout_download("Download timeout (30 min limit exceeded)"))
                    break

            # Check progress timeout (stalled download)
            if self.last_progress_time:
                time_since_progress = current_time - self.last_progress_time
                if time_since_progress > DOWNLOAD_PROGRESS_TIMEOUT:
                    logger.error(f"Download stalled (no progress for {DOWNLOAD_PROGRESS_TIMEOUT}s)")
                    self.root.after(0, lambda: self._timeout_download("Download stalled (no progress for 5 minutes)"))
                    break

    def _timeout_download(self, reason):
        """Handle download timeout"""
        if self.is_downloading:
            logger.warning(f"Timing out download: {reason}")
            self.update_status(reason, "red")
            self.stop_download()

    def stop_download(self):
        """Stop download gracefully, with forced termination as fallback"""
        if self.current_process and self.is_downloading:
            try:
                # Try graceful termination first (SIGTERM)
                self.current_process.terminate()

                # Wait for graceful shutdown
                try:
                    self.current_process.wait(timeout=PROCESS_TERMINATE_TIMEOUT)
                except subprocess.TimeoutExpired:
                    # If still running, force kill (SIGKILL)
                    logger.warning("Download process did not terminate gracefully, forcing kill")
                    self.current_process.kill()
                    self.current_process.wait()
            except Exception as e:
                logger.error(f"Error stopping download: {e}")

            self.is_downloading = False
            self.update_status("Download stopped", "orange")
            self.download_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            self.progress['value'] = 0
            self.progress_label.config(text="0%")

    def download(self, url):
        try:
            quality = self.quality_var.get()
            trim_enabled = self.trim_enabled_var.get()
            audio_only = (quality == "none")

            self.update_status("Starting download...", "blue")

            # Check if trimming is enabled and validate
            if trim_enabled:
                if self.video_duration <= 0:
                    self.update_status("Please fetch video duration first", "red")
                    self.download_btn.config(state='normal')
                    self.stop_btn.config(state='disabled')
                    self.is_downloading = False
                    return

                start_time = int(self.start_time_var.get())
                end_time = int(self.end_time_var.get())

                if start_time >= end_time:
                    self.update_status("Invalid time range", "red")
                    self.download_btn.config(state='normal')
                    self.stop_btn.config(state='disabled')
                    self.is_downloading = False
                    return

            if audio_only:
                # Generate filename with trim times if trimming is enabled
                if trim_enabled:
                    start_hms = self.seconds_to_hms(start_time).replace(':', '-')
                    end_hms = self.seconds_to_hms(end_time).replace(':', '-')
                    output_template = f'%(title)s_[{start_hms}_to_{end_hms}].%(ext)s'
                else:
                    output_template = '%(title)s.%(ext)s'

                cmd = [
                    self.ytdlp_path,
                    '-f', 'bestaudio',
                    '--extract-audio',
                    '--audio-format', 'm4a',
                    '--audio-quality', '128K',
                    '--newline',
                    '--progress',
                    '-o', os.path.join(self.download_path, output_template),
                ]

                # Add trimming for audio
                if trim_enabled:
                    cmd.extend([
                        '--postprocessor-args',
                        f'ffmpeg:-ss {start_time} -to {end_time}'
                    ])

                cmd.append(url)
            else:
                if quality == "none":
                    self.update_status("Please select a video quality", "red")
                    self.download_btn.config(state='normal')
                    self.stop_btn.config(state='disabled')
                    self.is_downloading = False
                    return

                height = quality

                # Generate filename with trim times if trimming is enabled
                if trim_enabled:
                    start_hms_file = self.seconds_to_hms(start_time).replace(':', '-')
                    end_hms_file = self.seconds_to_hms(end_time).replace(':', '-')
                    output_template = f'%(title)s_[{start_hms_file}_to_{end_hms_file}].%(ext)s'
                else:
                    output_template = '%(title)s.%(ext)s'

                cmd = [
                    self.ytdlp_path,
                    '-f', f'bestvideo[height<={height}]+bestaudio/best[height<={height}]',
                    '--merge-output-format', 'mp4',
                ]

                # Add trimming parameters
                if trim_enabled:
                    # Use download-sections for efficient trimming
                    start_hms = self.seconds_to_hms(start_time)
                    end_hms = self.seconds_to_hms(end_time)
                    cmd.extend([
                        '--download-sections', f'*{start_hms}-{end_hms}',
                        '--force-keyframes-at-cuts',
                    ])

                cmd.extend([
                    '--postprocessor-args', 'ffmpeg:-c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k',
                    '--newline',
                    '--progress',
                    '-o', os.path.join(self.download_path, output_template),
                    url
                ])

            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )

            # Parse output for progress
            for line in self.current_process.stdout:
                if not self.is_downloading:
                    break

                # Look for download progress
                if '[download]' in line and '%' in line:
                    # Parse progress percentage
                    progress_match = re.search(r'(\d+\.?\d*)%', line)
                    if progress_match:
                        progress = float(progress_match.group(1))
                        self.update_progress(progress)

                        # Try to extract speed and ETA from the line
                        status_msg = f"Downloading... {progress:.1f}%"

                        # Look for speed (e.g., "1.23MiB/s" or "500.00KiB/s")
                        speed_match = re.search(r'at\s+(\d+\.?\d*\s*[KMG]iB/s)', line)
                        if speed_match:
                            speed = speed_match.group(1)
                            status_msg += f" at {speed}"

                        # Look for ETA (e.g., "00:05" or "01:23:45")
                        eta_match = re.search(r'ETA\s+(\d{2}:\d{2}(?::\d{2})?)', line)
                        if eta_match:
                            eta = eta_match.group(1)
                            status_msg += f" | ETA: {eta}"

                        self.update_status(status_msg, "blue")
                        self.last_progress_time = time.time()  # Update progress timestamp

                # Look for post-processing
                elif '[Merger]' in line or 'Merging' in line:
                    self.update_status("Merging video and audio...", "blue")
                    self.last_progress_time = time.time()  # Update during post-processing
                elif 'Post-processing' in line:
                    self.update_status("Post-processing...", "blue")
                    self.last_progress_time = time.time()  # Update during post-processing

            self.current_process.wait()

            if self.current_process.returncode == 0 and self.is_downloading:
                self.update_progress(100)
                self.update_status("Download complete!", "green")
                logger.info(f"Download completed successfully: {url}")
            elif self.is_downloading:
                self.update_status("Download failed", "red")
                logger.error(f"Download failed with return code {self.current_process.returncode}")

        except FileNotFoundError as e:
            if self.is_downloading:
                error_msg = "yt-dlp or ffmpeg not found. Please ensure they are installed."
                self.update_status(error_msg, "red")
                logger.error(f"Dependency not found: {e}")
        except PermissionError as e:
            if self.is_downloading:
                error_msg = "Permission denied. Check write permissions for download folder."
                self.update_status(error_msg, "red")
                logger.error(f"Permission error: {e}")
        except OSError as e:
            if self.is_downloading:
                error_msg = f"OS error: {str(e)}"
                self.update_status(error_msg, "red")
                logger.error(f"OS error during download: {e}")
        except Exception as e:
            if self.is_downloading:
                self.update_status(f"Error: {str(e)}", "red")
                logger.exception(f"Unexpected error during download: {e}")

        finally:
            self.is_downloading = False
            self.download_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            self.current_process = None

    def update_progress(self, value):
        self.progress['value'] = value
        self.progress_label.config(text=f"{value:.1f}%")

    def update_status(self, message, color):
        self.status_label.config(text=message, foreground=color)

    def cleanup_temp_files(self):
        """Clean up temporary preview files"""
        try:
            import shutil
            # Clear cache references
            self._clear_preview_cache()
            # Remove temp directory
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")

    def on_closing(self):
        """Handle window close event"""
        # Stop any ongoing downloads gracefully
        if self.is_downloading and self.current_process:
            try:
                self.current_process.terminate()
                try:
                    self.current_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.current_process.kill()
            except Exception:
                pass

        # Clean up temp files
        self.cleanup_temp_files()

        # Shutdown thread pool
        logger.info("Shutting down thread pool...")
        self.thread_pool.shutdown(wait=False, cancel_futures=True)

        # Close the window
        self.root.destroy()

def main():
    root = tk.Tk()
    app = YouTubeDownloader(root)
    root.mainloop()

if __name__ == "__main__":
    main()
