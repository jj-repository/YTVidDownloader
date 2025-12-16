#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import subprocess
import threading
import re
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw, ImageFont
import tempfile
import time

class YouTubeDownloader:
    def __init__(self, root):
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

        # Frame preview variables
        self.start_preview_image = None
        self.end_preview_image = None
        self.temp_dir = tempfile.mkdtemp(prefix="ytdl_preview_")
        self.current_video_url = None
        self.preview_update_timer = None
        self.last_preview_update = 0

        # Find yt-dlp executable
        self.ytdlp_path = self.find_ytdlp()

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

        # Bind mousewheel to canvas and frame for scrolling anywhere
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind_all("<MouseWheel>", _on_mousewheel)

        main_frame = ttk.Frame(scrollable_frame, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(main_frame, text="YouTube URL:", font=('Arial', 12)).grid(row=0, column=0, sticky=tk.W, pady=(0, 10))

        self.url_entry = ttk.Entry(main_frame, width=60)
        self.url_entry.grid(row=1, column=0, columnspan=2, pady=(0, 20))

        # Video Quality section
        ttk.Label(main_frame, text="Video Quality:", font=('Arial', 11, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=(10, 5))

        self.quality_var = tk.StringVar(value="none")

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

        # Preview frame to hold both previews side by side
        preview_container = ttk.Frame(main_frame)
        preview_container.grid(row=15, column=0, sticky=tk.W, padx=(40, 0), pady=(10, 5))

        # Start time preview
        start_preview_frame = ttk.Frame(preview_container)
        start_preview_frame.grid(row=0, column=0, padx=(0, 20))

        ttk.Label(start_preview_frame, text="Start Time:", font=('Arial', 9)).pack()
        self.start_preview_label = tk.Label(start_preview_frame, bg='gray20', fg='white', relief='sunken')
        self.start_preview_label.pack(pady=(5, 0))

        # Create placeholder image
        self.placeholder_image = self.create_placeholder_image(240, 135, "Preview")
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
        start_control_frame.grid(row=16, column=0, sticky=tk.W, padx=(40, 0), pady=(2, 2))

        self.start_time_var = tk.DoubleVar(value=0)
        self.start_slider = ttk.Scale(start_control_frame, from_=0, to=100, variable=self.start_time_var,
                                      orient='horizontal', length=400, command=self.on_slider_change, state='disabled')
        self.start_slider.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(start_control_frame, text="Start:", font=('Arial', 9)).pack(side=tk.LEFT, padx=(0, 5))
        self.start_time_entry = ttk.Entry(start_control_frame, width=10, state='disabled')
        self.start_time_entry.pack(side=tk.LEFT)
        self.start_time_entry.insert(0, "00:00:00")
        self.start_time_entry.bind('<Return>', self.on_start_entry_change)
        self.start_time_entry.bind('<FocusOut>', self.on_start_entry_change)

        # End time slider and entry
        end_control_frame = ttk.Frame(main_frame)
        end_control_frame.grid(row=17, column=0, sticky=tk.W, padx=(40, 0), pady=(2, 2))

        self.end_time_var = tk.DoubleVar(value=100)
        self.end_slider = ttk.Scale(end_control_frame, from_=0, to=100, variable=self.end_time_var,
                                    orient='horizontal', length=400, command=self.on_slider_change, state='disabled')
        self.end_slider.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(end_control_frame, text="End:", font=('Arial', 9)).pack(side=tk.LEFT, padx=(0, 5))
        self.end_time_entry = ttk.Entry(end_control_frame, width=10, state='disabled')
        self.end_time_entry.pack(side=tk.LEFT)
        self.end_time_entry.insert(0, "00:00:00")
        self.end_time_entry.bind('<Return>', self.on_end_entry_change)
        self.end_time_entry.bind('<FocusOut>', self.on_end_entry_change)

        # Trim duration display
        self.trim_duration_label = ttk.Label(main_frame, text="Selected Duration: 00:00:00", foreground="green", font=('Arial', 9, 'bold'))
        self.trim_duration_label.grid(row=18, column=0, sticky=tk.W, padx=(40, 0), pady=(3, 0))

        ttk.Separator(main_frame, orient='horizontal').grid(row=19, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15)

        path_frame = ttk.Frame(main_frame)
        path_frame.grid(row=20, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(path_frame, text="Save to:").pack(side=tk.LEFT)
        self.path_label = ttk.Label(path_frame, text=self.download_path, foreground="blue")
        self.path_label.pack(side=tk.LEFT, padx=(10, 10))
        ttk.Button(path_frame, text="Change", command=self.change_path).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(path_frame, text="Open Folder", command=self.open_download_folder).pack(side=tk.LEFT)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=21, column=0, columnspan=2, pady=(0, 10))

        self.download_btn = ttk.Button(button_frame, text="Download", command=self.start_download)
        self.download_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_btn = ttk.Button(button_frame, text="Stop", command=self.stop_download, state='disabled')
        self.stop_btn.pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(main_frame, mode='determinate', length=560, maximum=100)
        self.progress.grid(row=22, column=0, columnspan=2)

        self.progress_label = ttk.Label(main_frame, text="0%", foreground="blue")
        self.progress_label.grid(row=23, column=0, columnspan=2, pady=(5, 0))

        self.status_label = ttk.Label(main_frame, text="Ready", foreground="green")
        self.status_label.grid(row=24, column=0, columnspan=2, pady=(10, 0))

    def create_placeholder_image(self, width, height, text):
        """Create a placeholder image with text"""
        img = Image.new('RGB', (width, height), color='#2d2d2d')
        draw = ImageDraw.Draw(img)

        # Draw text in center
        try:
            # Try to use a default font, fall back to default if not available
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except:
            font = ImageFont.load_default()

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

        if self.is_fetching_duration or self.is_downloading:
            return

        # Save the URL for preview extraction
        self.current_video_url = url

        self.is_fetching_duration = True
        self.fetch_duration_btn.config(state='disabled')
        self.update_status("Fetching video duration...", "blue")

        thread = threading.Thread(target=self.fetch_video_duration, args=(url,))
        thread.daemon = True
        thread.start()

    def fetch_video_duration(self, url):
        """Fetch video duration from URL"""
        try:
            cmd = [self.ytdlp_path, '--get-duration', url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

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

                self.update_status("Duration fetched successfully", "green")

                # Trigger initial preview update
                self.root.after(100, self.update_previews)
            else:
                raise Exception("Failed to fetch duration")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch video duration:\n{str(e)}")
            self.update_status("Failed to fetch duration", "red")

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

        # Schedule new update after 500ms of no slider movement
        self.preview_update_timer = self.root.after(500, self.update_previews)

    def extract_frame(self, timestamp):
        """Extract a single frame at the given timestamp"""
        if not self.current_video_url:
            return None

        try:
            # Create unique temp file for this frame
            temp_file = os.path.join(self.temp_dir, f"frame_{timestamp}.jpg")

            # Use yt-dlp to download just a small segment and extract frame
            cmd = [
                self.ytdlp_path,
                '-f', 'bestvideo[height<=480]/best[height<=480]',  # Lower quality for preview
                '--download-sections', f'*{timestamp}-{timestamp+2}',  # Just 2 seconds
                '--postprocessor-args', f'ffmpeg:-ss 1 -vframes 1 -q:v 2',
                '--exec', f'ffmpeg -i {{}} -ss 0 -vframes 1 -q:v 2 {temp_file}',
                '--no-keep-video',
                self.current_video_url
            ]

            # Alternative simpler approach using ffmpeg directly via yt-dlp
            cmd = [
                'ffmpeg',
                '-ss', str(timestamp),
                '-i', self.current_video_url,
                '-vframes', '1',
                '-q:v', '2',
                '-y',
                temp_file
            ]

            # Better: use yt-dlp to get stream URL and pipe to ffmpeg
            # Get the actual video URL
            get_url_cmd = [
                self.ytdlp_path,
                '-f', 'bestvideo[height<=480]/best[height<=480]',
                '-g',
                self.current_video_url
            ]

            result = subprocess.run(get_url_cmd, capture_output=True, text=True, timeout=15)
            if result.returncode != 0:
                return None

            video_url = result.stdout.strip().split('\n')[0]

            # Now extract frame from the actual stream
            cmd = [
                'ffmpeg',
                '-ss', str(timestamp),
                '-i', video_url,
                '-vframes', '1',
                '-q:v', '2',
                '-y',
                temp_file
            ]

            subprocess.run(cmd, capture_output=True, timeout=15, check=True)

            if os.path.exists(temp_file):
                return temp_file

        except Exception as e:
            print(f"Error extracting frame: {e}")

        return None

    def update_previews(self):
        """Update both preview images"""
        if not self.current_video_url or self.video_duration == 0:
            return

        start_time = int(self.start_time_var.get())
        end_time = int(self.end_time_var.get())

        # Update in a background thread to avoid blocking UI
        thread = threading.Thread(target=self._update_previews_thread, args=(start_time, end_time))
        thread.daemon = True
        thread.start()

    def _update_previews_thread(self, start_time, end_time):
        """Background thread to extract and update preview frames"""
        # Extract start frame
        start_frame_path = self.extract_frame(start_time)
        if start_frame_path:
            self._update_preview_image(start_frame_path, 'start')

        # Extract end frame
        end_frame_path = self.extract_frame(end_time)
        if end_frame_path:
            self._update_preview_image(end_frame_path, 'end')

    def _update_preview_image(self, image_path, position):
        """Update preview image in UI (must be called from main thread or scheduled)"""
        try:
            # Load and resize image
            img = Image.open(image_path)
            img.thumbnail((240, 135), Image.Resampling.LANCZOS)

            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)

            # Schedule UI update on main thread
            if position == 'start':
                self.root.after(0, lambda: self._set_start_preview(photo))
            else:
                self.root.after(0, lambda: self._set_end_preview(photo))

        except Exception as e:
            print(f"Error updating preview image: {e}")

    def _set_start_preview(self, photo):
        """Set start preview image (called on main thread)"""
        self.start_preview_image = photo  # Keep reference to avoid garbage collection
        self.start_preview_label.config(image=photo, text='')

    def _set_end_preview(self, photo):
        """Set end preview image (called on main thread)"""
        self.end_preview_image = photo  # Keep reference to avoid garbage collection
        self.end_preview_label.config(image=photo, text='')

    def change_path(self):
        path = filedialog.askdirectory(initialdir=self.download_path)
        if path:
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
        try:
            subprocess.run([self.ytdlp_path, '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def start_download(self):
        url = self.url_entry.get().strip()

        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return

        if not self.check_dependencies():
            messagebox.showerror("Error", "yt-dlp is not installed.\n\nInstall it with:\npip install yt-dlp")
            return

        self.is_downloading = True
        self.download_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.progress['value'] = 0
        self.progress_label.config(text="0%")

        thread = threading.Thread(target=self.download, args=(url,))
        thread.daemon = True
        thread.start()

    def stop_download(self):
        if self.current_process and self.is_downloading:
            self.current_process.kill()
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
                cmd = [
                    self.ytdlp_path,
                    '-f', 'bestaudio',
                    '--extract-audio',
                    '--audio-format', 'm4a',
                    '--audio-quality', '128K',
                    '--newline',
                    '--progress',
                    '-o', os.path.join(self.download_path, '%(title)s.%(ext)s'),
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
                    '-o', os.path.join(self.download_path, '%(title)s.%(ext)s'),
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
                    match = re.search(r'(\d+\.?\d*)%', line)
                    if match:
                        progress = float(match.group(1))
                        self.update_progress(progress)
                        self.update_status(f"Downloading... {progress:.1f}%", "blue")

                # Look for post-processing
                elif '[Merger]' in line or 'Merging' in line:
                    self.update_status("Merging video and audio...", "blue")
                elif 'Post-processing' in line:
                    self.update_status("Post-processing...", "blue")

            self.current_process.wait()

            if self.current_process.returncode == 0 and self.is_downloading:
                self.update_progress(100)
                self.update_status("Download complete!", "green")
            elif self.is_downloading:
                self.update_status("Download failed", "red")

        except Exception as e:
            if self.is_downloading:
                self.update_status(f"Error: {str(e)}", "red")

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
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Error cleaning up temp files: {e}")

    def on_closing(self):
        """Handle window close event"""
        # Stop any ongoing downloads
        if self.is_downloading and self.current_process:
            self.current_process.kill()

        # Clean up temp files
        self.cleanup_temp_files()

        # Close the window
        self.root.destroy()

def main():
    root = tk.Tk()
    app = YouTubeDownloader(root)
    root.mainloop()

if __name__ == "__main__":
    main()
