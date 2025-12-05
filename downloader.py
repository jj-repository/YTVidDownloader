#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import subprocess
import threading
import re
from pathlib import Path

class YouTubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YTVidDownloader")
        self.root.geometry("600x650")
        self.root.resizable(False, False)

        self.download_path = str(Path.home() / "Downloads")
        self.current_process = None
        self.is_downloading = False

        # Find yt-dlp executable
        self.ytdlp_path = self.find_ytdlp()

        self.setup_ui()

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
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(main_frame, text="YouTube URL:", font=('Arial', 12)).grid(row=0, column=0, sticky=tk.W, pady=(0, 10))

        self.url_entry = ttk.Entry(main_frame, width=60)
        self.url_entry.grid(row=1, column=0, columnspan=2, pady=(0, 20))

        ttk.Label(main_frame, text="Video Quality:", font=('Arial', 11, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=(10, 5))

        self.quality_var = tk.StringVar(value="none")

        ttk.Radiobutton(main_frame, text="1440p (2560x1440)", variable=self.quality_var, value="1440").grid(row=3, column=0, sticky=tk.W, padx=(20, 0))
        ttk.Radiobutton(main_frame, text="1080p (1920x1080)", variable=self.quality_var, value="1080").grid(row=4, column=0, sticky=tk.W, padx=(20, 0))
        ttk.Radiobutton(main_frame, text="720p (1280x720)", variable=self.quality_var, value="720").grid(row=5, column=0, sticky=tk.W, padx=(20, 0))
        ttk.Radiobutton(main_frame, text="480p (854x480)", variable=self.quality_var, value="480").grid(row=6, column=0, sticky=tk.W, padx=(20, 0))
        ttk.Radiobutton(main_frame, text="360p (640x360)", variable=self.quality_var, value="360").grid(row=7, column=0, sticky=tk.W, padx=(20, 0))
        ttk.Radiobutton(main_frame, text="240p (426x240)", variable=self.quality_var, value="240").grid(row=8, column=0, sticky=tk.W, padx=(20, 0))
        ttk.Radiobutton(main_frame, text="None (Audio only)", variable=self.quality_var, value="none").grid(row=9, column=0, sticky=tk.W, padx=(20, 0))

        ttk.Separator(main_frame, orient='horizontal').grid(row=10, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=20)

        ttk.Label(main_frame, text="Audio Options:", font=('Arial', 11, 'bold')).grid(row=11, column=0, sticky=tk.W, pady=(0, 5))

        self.audio_only_var = tk.BooleanVar()
        ttk.Checkbutton(main_frame, text="Extract audio only (M4A format)", variable=self.audio_only_var,
                       command=self.toggle_audio_only).grid(row=12, column=0, sticky=tk.W, padx=(20, 0))

        ttk.Separator(main_frame, orient='horizontal').grid(row=13, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=20)

        path_frame = ttk.Frame(main_frame)
        path_frame.grid(row=14, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))

        ttk.Label(path_frame, text="Save to:").pack(side=tk.LEFT)
        self.path_label = ttk.Label(path_frame, text=self.download_path, foreground="blue")
        self.path_label.pack(side=tk.LEFT, padx=(10, 10))
        ttk.Button(path_frame, text="Change", command=self.change_path).pack(side=tk.LEFT)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=15, column=0, columnspan=2, pady=(0, 10))

        self.download_btn = ttk.Button(button_frame, text="Download", command=self.start_download)
        self.download_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_btn = ttk.Button(button_frame, text="Stop", command=self.stop_download, state='disabled')
        self.stop_btn.pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(main_frame, mode='determinate', length=560, maximum=100)
        self.progress.grid(row=16, column=0, columnspan=2)

        self.progress_label = ttk.Label(main_frame, text="0%", foreground="blue")
        self.progress_label.grid(row=17, column=0, columnspan=2, pady=(5, 0))

        self.status_label = ttk.Label(main_frame, text="Ready", foreground="green")
        self.status_label.grid(row=18, column=0, columnspan=2, pady=(10, 0))

    def toggle_audio_only(self):
        if self.audio_only_var.get():
            self.quality_var.set("none")

    def change_path(self):
        path = filedialog.askdirectory(initialdir=self.download_path)
        if path:
            self.download_path = path
            self.path_label.config(text=path)

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
            audio_only = self.audio_only_var.get()
            quality = self.quality_var.get()

            self.update_status("Starting download...", "blue")

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
                    url
                ]
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
                    '--postprocessor-args', 'ffmpeg:-c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k',
                    '--newline',
                    '--progress',
                    '-o', os.path.join(self.download_path, '%(title)s.%(ext)s'),
                    url
                ]

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

def main():
    root = tk.Tk()
    app = YouTubeDownloader(root)
    root.mainloop()

if __name__ == "__main__":
    main()
