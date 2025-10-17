#!/usr/bin/env python3
"""
HTML5 to Video Converter - Streamlit App
Auto-detection of parameters with manual override option
"""

import streamlit as st
import os
import tempfile
import zipfile
from pathlib import Path
import time
import subprocess
import shutil
from dataclasses import dataclass
import re
from typing import Optional, Tuple
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


@dataclass
class VideoConfig:
    """Configuration for video output"""
    width: int
    height: int
    fps: int
    duration: int
    codec: str = "libx264"
    bitrate: str = "10M"
    animation_speed: float = 0.85  # 0.85 = 15% slower, 1.0 = normal speed
    preset: str = "slow"
    crf: int = 18


class HTML5Analyzer:
    """Analyzes HTML5 content to auto-detect optimal settings"""

    @staticmethod
    def analyze_html(html_path: str) -> dict:
        """Analyze HTML file to detect resolution and animation duration"""

        with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Default values
        width = 1920
        height = 1080
        duration = 10
        fps = 60

        # Try to find viewport/canvas dimensions
        viewport_patterns = [
            r'viewport.*width["\s:=]+(\d+)',
            r'width:\s*(\d+)px',
            r'canvas.*width["\s:=]+(\d+)',
            r'<meta.*content=.*width=(\d+)',
        ]

        height_patterns = [
            r'viewport.*height["\s:=]+(\d+)',
            r'height:\s*(\d+)px',
            r'canvas.*height["\s:=]+(\d+)',
            r'<meta.*content=.*height=(\d+)',
        ]

        for pattern in viewport_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                detected_width = int(match.group(1))
                if 100 <= detected_width <= 7680:
                    width = detected_width
                    break

        for pattern in height_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                detected_height = int(match.group(1))
                if 100 <= detected_height <= 4320:
                    height = detected_height
                    break

        # Try to detect animation duration
        duration_patterns = [
            r'duration["\s:=]+(\d+)',
            r'animation.*?(\d+)s',
            r'setTimeout.*?(\d+)\s*\*\s*1000',
        ]

        for pattern in duration_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                durations = [int(m) for m in matches if int(m) < 1000]
                if durations:
                    detected_duration = max(durations)
                    # Cap at 20 seconds max (most animations complete within 15s)
                    # This prevents false positives from picking up large timeouts
                    duration = min(detected_duration, 20)
                    break

        # Detect if high FPS needed (check for animation-heavy content)
        animation_keywords = ['animation', 'transition', 'transform', 'requestAnimationFrame']
        animation_count = sum(content.lower().count(kw) for kw in animation_keywords)

        if animation_count > 10:
            fps = 60  # Smooth animations
        elif animation_count > 3:
            fps = 30  # Standard
        else:
            fps = 24  # Basic

        return {
            'width': width,
            'height': height,
            'duration': duration,
            'fps': fps,
            'detected': animation_count > 0
        }


class FormatCSS:
    """CSS templates for social media formats"""

    @staticmethod
    def generate_css(width: int, height: int, source_width: int, source_height: int, bg_color: str = "#000000") -> str:
        """Generate CSS for wrapping and scaling content"""

        # Calculate scale to fit
        scale_x = width / source_width
        scale_y = height / source_height
        scale = min(scale_x, scale_y)  # preserve aspect ratio

        # Calculate final scaled size
        scaled_w = source_width * scale
        scaled_h = source_height * scale

        # Calculate offsets to center
        offset_x = (width - scaled_w) / 2
        offset_y = (height - scaled_h) / 2

        return f"""
        <style id="format-override">
        html, body {{
            margin: 0 !important;
            padding: 0 !important;
            width: {width}px !important;
            height: {height}px !important;
            overflow: hidden !important;
            background: {bg_color} !important;
        }}
        #__scale_wrapper__ {{
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            width: {source_width}px !important;
            height: {source_height}px !important;
            transform: scale({scale}) translate({offset_x/scale}px, {offset_y/scale}px) !important;
            transform-origin: top left !important;
            overflow: visible !important;
        }}
        </style>
        """

    @staticmethod
    def detect_best_format(source_width: int, source_height: int) -> tuple:
        """
        Detect best social media format based on source aspect ratio.
        Returns (width, height, format_name)
        """
        source_aspect = source_width / source_height

        # 1:1 square format
        square_aspect = 1.0
        # 9:16 vertical format
        vertical_aspect = 9.0 / 16.0

        # Calculate how far source is from each format
        diff_square = abs(source_aspect - square_aspect)
        diff_vertical = abs(source_aspect - vertical_aspect)

        # Choose closest format
        if diff_square < diff_vertical:
            return (1080, 1080, "1080x1080 (Square/Instagram)")
        else:
            return (1080, 1920, "1080x1920 (Vertical/Stories)")


class SmartUpscaler:
    """Handles smart aspect ratio fitting and upscaling"""

    @staticmethod
    def calculate_fit_dimensions(source_w: int, source_h: int, target_w: int, target_h: int) -> dict:
        """
        Calculate dimensions to fit source into target without distortion.
        Returns dict with fitted dimensions and padding.
        """
        source_aspect = source_w / source_h
        target_aspect = target_w / target_h

        if abs(source_aspect - target_aspect) < 0.01:
            # Aspects are nearly identical, just scale
            return {
                'fit_width': target_w,
                'fit_height': target_h,
                'pad_top': 0,
                'pad_bottom': 0,
                'pad_left': 0,
                'pad_right': 0,
                'needs_padding': False
            }

        if source_aspect > target_aspect:
            # Source is wider → fit width, add top/bottom bars
            fit_width = target_w
            fit_height = int(target_w / source_aspect)
            # Ensure even dimensions
            if fit_height % 2 != 0:
                fit_height -= 1
            pad_top = (target_h - fit_height) // 2
            pad_bottom = target_h - fit_height - pad_top
            return {
                'fit_width': fit_width,
                'fit_height': fit_height,
                'pad_top': pad_top,
                'pad_bottom': pad_bottom,
                'pad_left': 0,
                'pad_right': 0,
                'needs_padding': True
            }
        else:
            # Source is taller → fit height, add left/right bars
            fit_height = target_h
            fit_width = int(target_h * source_aspect)
            # Ensure even dimensions
            if fit_width % 2 != 0:
                fit_width -= 1
            pad_left = (target_w - fit_width) // 2
            pad_right = target_w - fit_width - pad_left
            return {
                'fit_width': fit_width,
                'fit_height': fit_height,
                'pad_top': 0,
                'pad_bottom': 0,
                'pad_left': pad_left,
                'pad_right': pad_right,
                'needs_padding': True
            }

    @staticmethod
    def get_ffmpeg_scale_filter(source_w: int, source_h: int, target_w: int, target_h: int,
                                 enable_upscaling: bool = False) -> str:
        """
        Generate FFmpeg scale filter with smart fitting and optional advanced upscaling.
        Uses lanczos for high quality, adds unsharp for crispness.
        """
        fit_info = SmartUpscaler.calculate_fit_dimensions(source_w, source_h, target_w, target_h)

        # Calculate scale factor
        scale_factor_w = target_w / source_w
        scale_factor_h = target_h / source_h
        scale_factor = max(scale_factor_w, scale_factor_h)

        # Choose scaler based on scale factor and upscaling setting
        if enable_upscaling and scale_factor > 1.5:
            # Use spline36 for better upscaling (better than lanczos for large scales)
            scaler = "spline36"
            # Stronger sharpening for upscaled content
            sharpen = "unsharp=7:7:1.5:7:7:0.0"
        else:
            # Use lanczos for normal scaling
            scaler = "lanczos"
            # Normal sharpening
            sharpen = "unsharp=5:5:1.0:5:5:0.0"

        if fit_info['needs_padding']:
            # Scale to fit dimensions, then pad to target
            filter_parts = [
                f"scale={fit_info['fit_width']}:{fit_info['fit_height']}:flags={scaler}",
                sharpen,
                f"pad={target_w}:{target_h}:{fit_info['pad_left']}:{fit_info['pad_top']}:black"
            ]
            return ",".join(filter_parts)
        else:
            # Just scale and sharpen
            filter_parts = [
                f"scale={target_w}:{target_h}:flags={scaler}",
                sharpen
            ]
            return ",".join(filter_parts)


class HTML5ToVideoConverter:
    """Main converter class"""

    def __init__(self, progress_callback=None):
        self.cancelled = False
        self.progress_callback = progress_callback
        self.debug_log = []  # Collect all debug output
        import datetime
        self.start_time = datetime.datetime.now()

    def update_progress(self, value, message=None):
        """Update external progress if callback provided"""
        if self.progress_callback:
            self.progress_callback(value, message)

    def log(self, message):
        """Add message to debug log"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] {message}"
        self.debug_log.append(log_entry)
        return log_entry

    def get_debug_output(self):
        """Get all debug output as terminal-style text"""
        return "\n".join(self.debug_log)

    def _get_elapsed_time(self):
        """Get elapsed time since conversion started"""
        import datetime
        elapsed = datetime.datetime.now() - self.start_time
        return f"{elapsed.total_seconds():.2f}s"

    def extract_zip(self, zip_path: str, extract_dir: str) -> str:
        """Extract and find main HTML file"""
        self.update_progress(0.1, "Extracting...")
        self.log(f"=== ZIP EXTRACTION ===")
        self.log(f"ZIP path: {zip_path}")
        self.log(f"Extract to: {extract_dir}")

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            files = zip_ref.namelist()

            # Validate empty ZIP
            if len(files) == 0:
                self.log("ERROR: ZIP file is empty")
                raise ValueError("ZIP file is empty")

            # Validate file count (prevent excessive files)
            if len(files) > 1000:
                self.log(f"ERROR: ZIP contains too many files ({len(files)})")
                raise ValueError(f"ZIP contains too many files ({len(files)}). Maximum 1000 files allowed.")

            # Calculate total uncompressed size (prevent ZIP bombs)
            total_size = sum(info.file_size for info in zip_ref.infolist())
            max_uncompressed = 50 * 1024 * 1024  # 50MB uncompressed

            if total_size > max_uncompressed:
                size_mb = total_size / (1024 * 1024)
                self.log(f"ERROR: Uncompressed size too large ({size_mb:.1f} MB)")
                raise ValueError(f"Uncompressed size too large ({size_mb:.1f} MB). Maximum 50 MB allowed.")

            self.log(f"ZIP contains {len(files)} files")
            self.log(f"Total uncompressed size: {total_size / (1024 * 1024):.1f} MB")

            # Validate all paths for security (prevent path traversal)
            for file in files:
                # Normalize path and check for traversal attempts
                normalized = os.path.normpath(file)
                if normalized.startswith('..') or os.path.isabs(normalized):
                    self.log(f"ERROR: Unsafe file path detected: {file}")
                    raise ValueError(f"Unsafe file path in ZIP: {file}")

            # Safe to extract now
            zip_ref.extractall(extract_dir)
            self.log(f"Extracted all files successfully")

        html_files = list(Path(extract_dir).rglob("*.html"))
        self.log(f"Found {len(html_files)} HTML files")

        if not html_files:
            self.log("ERROR: No HTML files found in archive")
            raise FileNotFoundError("No HTML files found in the archive")

        # Look for index.html or use first HTML file
        main_html = None
        for html_file in html_files:
            self.log(f"  - {html_file.name}")
            if html_file.name.lower() in ['index.html', 'index.htm']:
                main_html = html_file
                break

        if not main_html:
            main_html = html_files[0]

        self.log(f"Using main HTML: {main_html.name}")
        self.log(f"Absolute path: {main_html.absolute()}")
        return str(main_html.absolute())

    def render_html_to_frames(self, html_path: str, output_dir: str, config: VideoConfig) -> Optional[str]:
        """Render HTML to frames with guaranteed correct dimensions"""
        from PIL import Image

        self.update_progress(0.2, "Loading browser...")

        frames_dir = os.path.join(output_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)

        total_frames = config.fps * config.duration
        frame_time_s = 1.0 / config.fps

        # Auto-detect best social media format based on source dimensions
        self.log(f"=== HTML5 TO VIDEO RENDERING ===")
        self.log(f"Source dimensions: {config.width}x{config.height}")

        # Always use social media format (auto-detect best fit)
        target_width, target_height, format_name = FormatCSS.detect_best_format(config.width, config.height)
        source_aspect = config.width / config.height
        target_aspect = target_width / target_height

        self.log(f"Source aspect ratio: {source_aspect:.3f} ({config.width}:{config.height})")
        self.log(f"Auto-detected best format: {format_name}")
        self.log(f"Target aspect ratio: {target_aspect:.3f} ({target_width}:{target_height})")
        self.log(f"Target dimensions: {target_width}x{target_height}")
        self.log(f"Total frames: {total_frames} ({config.fps} FPS × {config.duration}s)")
        self.log(f"Frame time: {frame_time_s:.4f}s per frame")
        self.log(f"Animation speed: {config.animation_speed}x ({int((1-config.animation_speed)*100)}% slower)" if config.animation_speed < 1.0 else f"Animation speed: {config.animation_speed}x ({int((config.animation_speed-1)*100)}% faster)" if config.animation_speed > 1.0 else "Animation speed: 1.0x (normal)")

        # Calculate PROPORTIONAL scale factor BEFORE browser setup
        scale_factor_w = target_width / config.width
        scale_factor_h = target_height / config.height
        scale_factor = min(scale_factor_w, scale_factor_h)  # Use min to fit within target (PROPORTIONAL)
        needs_format_change = (target_width != config.width or target_height != config.height)

        # Calculate actual scaled dimensions (maintaining aspect ratio)
        scaled_width = int(config.width * scale_factor)
        scaled_height = int(config.height * scale_factor)

        # Calculate padding needed to center in target frame
        pad_x = (target_width - scaled_width) // 2
        pad_y = (target_height - scaled_height) // 2

        self.log(f"Scale factor: {scale_factor:.2f}x (PROPORTIONAL - maintains aspect ratio)")
        self.log(f"Source: {config.width}x{config.height} → Scaled: {scaled_width}x{scaled_height}")
        self.log(f"Target frame: {target_width}x{target_height}")
        self.log(f"Padding: {pad_x}px horizontal, {pad_y}px vertical")
        self.log(f"Format change needed: {needs_format_change}")

        # Chrome options - REQUIREMENT #1: Set window size to TARGET with buffer for centering
        self.log(f"=== BROWSER INITIALIZATION ===")
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--hide-scrollbars')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')

        # Set window to TARGET resolution (where we'll render centered content)
        # We'll use CSS transform to scale content proportionally and center it
        window_size = f'{target_width},{target_height}'
        chrome_options.add_argument(f'--window-size={window_size}')
        chrome_options.add_argument('--force-device-scale-factor=1')  # No device scaling, we handle it with CSS
        self.log(f"Chrome --window-size: {window_size} (target frame)")
        self.log(f"Will use CSS transform for proportional scaling")

        # Find browser binary
        browser_paths = [
            "/Applications/Comet.app/Contents/MacOS/Comet",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/usr/bin/google-chrome"
        ]

        browser_found = None
        for path in browser_paths:
            if os.path.exists(path):
                chrome_options.binary_location = path
                browser_found = path
                self.log(f"Found browser: {path}")
                break

        if not browser_found:
            self.log("WARNING: No browser binary found, using system default")

        try:
            self.log("Creating WebDriver instance...")
            driver = webdriver.Chrome(options=chrome_options)
            self.log("WebDriver created successfully")

            # Set timeouts to prevent hanging
            driver.set_page_load_timeout(30)  # 30 second page load timeout
            driver.set_script_timeout(10)     # 10 second script execution timeout
            self.log("Timeouts set: 30s page load, 10s script execution")
        except Exception as e:
            self.log(f"ERROR: Failed to create WebDriver: {e}")
            return None

        try:
            # Set window to TARGET resolution via Selenium
            self.log(f"=== PAGE LOADING ===")
            driver.set_window_size(target_width, target_height)
            self.log(f"Selenium set_window_size called: {target_width}x{target_height} (target frame)")

            # Load HTML
            file_url = f"file://{html_path}"
            self.log(f"Loading URL: {file_url}")
            driver.get(file_url)
            self.log(f"Page loaded")

            # Extract background color and apply minimal CSS for high-res rendering
            bg_color_hex = "#000000"  # default
            if needs_format_change:
                self.log(f"=== HIGH-RESOLUTION RENDERING SETUP ===")
                self.log(f"Target format: {format_name}")

                # Extract predominant background color from page
                try:
                    bg_color_js = """
                        function getPredominantColor() {
                            // Try body background color first
                            let bodyBg = window.getComputedStyle(document.body).backgroundColor;
                            if (bodyBg && bodyBg !== 'rgba(0, 0, 0, 0)' && bodyBg !== 'transparent') {
                                return bodyBg;
                            }

                            // Try html background color
                            let htmlBg = window.getComputedStyle(document.documentElement).backgroundColor;
                            if (htmlBg && htmlBg !== 'rgba(0, 0, 0, 0)' && htmlBg !== 'transparent') {
                                return htmlBg;
                            }

                            // Try first div or main content container
                            let containers = document.querySelectorAll('div, main, section, #banner, .frame');
                            for (let el of containers) {
                                let bg = window.getComputedStyle(el).backgroundColor;
                                if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') {
                                    return bg;
                                }
                            }

                            // Default to black
                            return 'rgb(0, 0, 0)';
                        }
                        return getPredominantColor();
                    """
                    bg_color_rgb = driver.execute_script(bg_color_js)

                    # Convert RGB to hex
                    if bg_color_rgb and bg_color_rgb.startswith('rgb'):
                        import re
                        rgb_match = re.search(r'(\d+),\s*(\d+),\s*(\d+)', bg_color_rgb)
                        if rgb_match:
                            r, g, b = map(int, rgb_match.groups())
                            bg_color_hex = f"#{r:02x}{g:02x}{b:02x}"
                        else:
                            bg_color_hex = "#000000"
                    else:
                        bg_color_hex = bg_color_rgb if bg_color_rgb else "#000000"

                    self.log(f"Detected background color: {bg_color_rgb} → {bg_color_hex}")
                except Exception as e:
                    self.log(f"Could not detect background color, using black: {e}")
                    bg_color_hex = "#000000"

                # Log proportional scaling strategy
                self.log(f"=== PROPORTIONAL SCALING STRATEGY ===")
                self.log(f"Browser viewport: {target_width}x{target_height} (target frame)")
                self.log(f"Source content: {config.width}x{config.height}")
                self.log(f"Proportional scale: {scale_factor:.3f}x (uniform)")
                self.log(f"Scaled content: {scaled_width}x{scaled_height}")
                self.log(f"Centering with padding: {pad_x}px H, {pad_y}px V")
                self.log(f"Background color: {bg_color_hex}")

                # PROPORTIONAL CSS transform scaling with FORCED viewport dimensions
                proportional_scaling = f"""
                    console.log('Setting up PROPORTIONAL scaling with FORCED viewport centering');

                    // FORCE viewport to EXACT target frame size
                    document.documentElement.style.margin = '0';
                    document.documentElement.style.padding = '0';
                    document.documentElement.style.width = '{target_width}px';
                    document.documentElement.style.height = '{target_height}px';
                    document.documentElement.style.minHeight = '{target_height}px';
                    document.documentElement.style.maxHeight = '{target_height}px';
                    document.documentElement.style.overflow = 'hidden';
                    document.documentElement.style.background = '{bg_color_hex}';

                    // FORCE body to EXACT target frame size (critical for centering!)
                    document.body.style.margin = '0';
                    document.body.style.padding = '0';
                    document.body.style.width = '{target_width}px';
                    document.body.style.height = '{target_height}px';
                    document.body.style.minHeight = '{target_height}px';
                    document.body.style.maxHeight = '{target_height}px';
                    document.body.style.overflow = 'hidden';
                    document.body.style.background = '{bg_color_hex}';
                    document.body.style.position = 'relative';  // For absolute positioning context

                    // Create wrapper for scaled content
                    var wrapper = document.createElement('div');
                    wrapper.id = '__content_wrapper__';

                    // CRITICAL: Position at calculated offset for perfect centering
                    wrapper.style.position = 'absolute';
                    wrapper.style.left = '{pad_x}px';     // Horizontal centering offset
                    wrapper.style.top = '{pad_y}px';      // Vertical centering offset (e.g., 150px for 320x480→1080x1920)
                    wrapper.style.width = '{config.width}px';
                    wrapper.style.height = '{config.height}px';

                    // Transform from top-left origin (wrapper already positioned correctly)
                    wrapper.style.transform = 'scale({scale_factor})';
                    wrapper.style.transformOrigin = 'top left';

                    // Move all body children into wrapper
                    while (document.body.firstChild) {{
                        wrapper.appendChild(document.body.firstChild);
                    }}
                    document.body.appendChild(wrapper);

                    // CRITICAL: Scale canvas internal buffers for sharp rendering
                    var canvases = wrapper.getElementsByTagName('canvas');
                    for (var i = 0; i < canvases.length; i++) {{
                        var canvas = canvases[i];
                        var origW = canvas.width;
                        var origH = canvas.height;

                        // Scale internal buffer to high-res
                        canvas.width = Math.floor(origW * {scale_factor});
                        canvas.height = Math.floor(origH * {scale_factor});

                        // Set CSS size to match original layout
                        canvas.style.width = origW + 'px';
                        canvas.style.height = origH + 'px';

                        console.log('Scaled canvas buffer:', origW + 'x' + origH, '→', canvas.width + 'x' + canvas.height);

                        // Try to trigger redraw
                        if (window.render) window.render();
                        if (canvas.render) canvas.render();
                    }}

                    console.log('FORCED viewport centering complete');
                    console.log('Viewport: FORCED to {target_width}x{target_height}');
                    console.log('Wrapper position: absolute, left:{pad_x}px, top:{pad_y}px');
                    console.log('Transform: scale({scale_factor}) from top-left');
                    console.log('Result: {scaled_width}x{scaled_height} centered in {target_width}x{target_height} frame');
                """
                driver.execute_script(proportional_scaling)
                self.log(f"Applied PROPORTIONAL scaling with FORCED viewport dimensions")
            else:
                # No format change needed - use original dimensions
                self.log(f"=== STANDARD RENDERING ===")
                js_standard = f"""
                    document.documentElement.style.margin = '0';
                    document.documentElement.style.padding = '0';
                    document.documentElement.style.overflow = 'hidden';

                    document.body.style.margin = '0';
                    document.body.style.padding = '0';
                    document.body.style.overflow = 'hidden';
                """
                driver.execute_script(js_standard)
                self.log(f"Using standard rendering at {config.width}x{config.height}")

            # REQUIREMENT #4: Delay for page to settle
            self.log("Waiting 1.5s for page to settle...")
            time.sleep(1.5)
            self.log("Wait complete")

            # REQUIREMENT #5: Log detected, requested, and actual dimensions
            actual_viewport_w = driver.execute_script("return window.innerWidth;")
            actual_viewport_h = driver.execute_script("return window.innerHeight;")
            actual_body_w = driver.execute_script("return document.body.offsetWidth;")
            actual_body_h = driver.execute_script("return document.body.offsetHeight;")

            # Log dimension analysis
            self.log(f"=== DIMENSION ANALYSIS ===")
            self.log(f"Native HTML5 size: {config.width}x{config.height}")
            self.log(f"Target output size: {target_width}x{target_height}")
            self.log(f"Actual viewport: {actual_viewport_w}x{actual_viewport_h}")
            self.log(f"Actual body: {actual_body_w}x{actual_body_h}")

            if needs_format_change:
                hires_match = 'YES' if actual_viewport_w == target_width and actual_viewport_h == target_height else 'NO'
                self.log(f"High-res viewport match: {hires_match}")
                if actual_viewport_w != target_width or actual_viewport_h != target_height:
                    self.log(f"WARNING: Viewport mismatch! Expected {target_width}x{target_height}, got {actual_viewport_w}x{actual_viewport_h}")
                    self.log(f"CORRECTING viewport dimensions...")

                    # CRITICAL FIX: Force viewport to exact dimensions
                    # Chrome subtracts UI chrome, we need to compensate
                    height_diff = target_height - actual_viewport_h
                    width_diff = target_width - actual_viewport_w

                    self.log(f"Height shortfall: {height_diff}px, Width shortfall: {width_diff}px")

                    # Resize window to compensate for Chrome UI
                    corrected_width = target_width + width_diff
                    corrected_height = target_height + height_diff

                    self.log(f"Resizing window to: {corrected_width}x{corrected_height} (to achieve {target_width}x{target_height} viewport)")
                    driver.set_window_size(corrected_width, corrected_height)

                    # Wait for resize
                    time.sleep(0.5)

                    # Verify correction
                    new_viewport_w = driver.execute_script("return window.innerWidth;")
                    new_viewport_h = driver.execute_script("return window.innerHeight;")
                    self.log(f"After correction: {new_viewport_w}x{new_viewport_h}")

                    if new_viewport_w == target_width and new_viewport_h == target_height:
                        self.log(f"SUCCESS: Viewport corrected successfully!")
                    else:
                        self.log(f"WARNING: Viewport still mismatched, will continue anyway")
            else:
                native_match = 'YES' if actual_viewport_w == config.width and actual_viewport_h == config.height else 'NO'
                self.log(f"Native size match: {native_match}")
                if actual_viewport_w != config.width or actual_viewport_h != config.height:
                    self.log(f"WARNING: Viewport mismatch! Expected {config.width}x{config.height}, got {actual_viewport_w}x{actual_viewport_h}")

            # Trigger animations and prepare for recording
            self.log(f"=== ANIMATION SETUP ===")
            self.log("Triggering animations and interactive elements...")

            # Execute JavaScript to start animations and simulate interactions
            animation_trigger_script = """
                // Force all CSS animations to run and apply hover states
                var style = document.createElement('style');
                style.innerHTML = `
                    * {
                        animation-play-state: running !important;
                        animation-delay: 0s !important;
                    }

                    /* Force hover states to be visible (for interactive demos) */
                    *:hover,
                    .amount:hover,
                    .button:hover {
                        /* Apply hover styles permanently for demo */
                    }
                `;
                document.head.appendChild(style);

                // Force first interactive element to appear hovered
                var firstInteractive = document.querySelector('.button, .amount, [class*="hover"]');
                if (firstInteractive) {
                    firstInteractive.classList.add('force-hover');
                    var hoverStyle = document.createElement('style');
                    hoverStyle.innerHTML = '.force-hover { /* hover styles will be applied */ }';
                    document.head.appendChild(hoverStyle);
                }

                // Simulate hover on all interactive elements
                var interactiveElements = document.querySelectorAll('a, button, [class*="hover"], [class*="interactive"]');
                interactiveElements.forEach(function(el) {
                    el.dispatchEvent(new MouseEvent('mouseover', {bubbles: true, cancelable: true}));
                    el.dispatchEvent(new MouseEvent('mouseenter', {bubbles: true, cancelable: true}));
                });

                // Click the body to trigger any click-based animations
                document.body.click();
                document.body.dispatchEvent(new MouseEvent('mouseover', {bubbles: true}));

                // Trigger common animation start functions
                if (typeof startAnimation === 'function') startAnimation();
                if (typeof start === 'function') start();
                if (typeof init === 'function') init();
                if (typeof play === 'function') play();
                if (typeof animate === 'function') animate();

                // CreateJS/EaselJS support (common in HTML5 ads)
                if (typeof createjs !== 'undefined' && createjs.Ticker) {
                    console.log('CreateJS detected, setting up ticker');
                    window.__createJSActive = true;
                    if (!createjs.Ticker.hasEventListener('tick')) {
                        console.log('CreateJS ticker not started, starting now');
                        createjs.Ticker.framerate = 30;
                        createjs.Ticker.timingMode = createjs.Ticker.RAF;
                    }
                }

                // GSAP support
                if (typeof gsap !== 'undefined') {
                    console.log('GSAP detected');
                    window.__gsapActive = true;
                }

                // For canvas/WebGL animations
                window.animationStartTime = Date.now();
                window.animationEnabled = true;

                // Trigger any paused videos
                var videos = document.getElementsByTagName('video');
                for (var i = 0; i < videos.length; i++) {
                    videos[i].play();
                }

                // Look for canvas elements and try to find their animation context
                var canvases = document.getElementsByTagName('canvas');
                console.log('Found ' + canvases.length + ' canvas elements');
                for (var i = 0; i < canvases.length; i++) {
                    console.log('Canvas ' + i + ': ' + canvases[i].width + 'x' + canvases[i].height);
                }
            """
            driver.execute_script(animation_trigger_script)
            time.sleep(0.5)  # Give animations time to initialize

            # Capture console logs to see what was detected
            logs = driver.get_log('browser')
            for log in logs:
                if 'CreateJS' in log['message'] or 'GSAP' in log['message'] or 'canvas' in log['message'].lower():
                    self.log(f"Browser console: {log['message']}")

            # Check what CSS animations exist
            animations_info = driver.execute_script("""
                var info = {
                    stylesheets: document.styleSheets.length,
                    animations: []
                };

                // Try to find @keyframes rules
                try {
                    for (var i = 0; i < document.styleSheets.length; i++) {
                        var sheet = document.styleSheets[i];
                        try {
                            var rules = sheet.cssRules || sheet.rules;
                            for (var j = 0; j < rules.length; j++) {
                                if (rules[j].type === CSSRule.KEYFRAMES_RULE) {
                                    info.animations.push(rules[j].name);
                                }
                            }
                        } catch(e) {
                            // CORS or access issues
                        }
                    }
                } catch(e) {}

                // Check computed styles on elements
                var elements = document.querySelectorAll('*');
                info.animated_elements = 0;
                for (var i = 0; i < elements.length; i++) {
                    var style = window.getComputedStyle(elements[i]);
                    if (style.animationName && style.animationName !== 'none') {
                        info.animated_elements++;
                    }
                }

                return info;
            """)

            self.log(f"CSS info: {animations_info['stylesheets']} stylesheets, {len(animations_info['animations'])} keyframe animations")
            if animations_info['animations']:
                self.log(f"Keyframes found: {', '.join(animations_info['animations'])}")
            self.log(f"Elements with animations: {animations_info['animated_elements']}")

            self.log("Animations triggered")

            # Let animations run briefly to establish initial random states
            time.sleep(0.1)
            self.log("Allowed 0.1s for animations to initialize")

            # Now pause and take control using Web Animations API for better control
            driver.execute_script("""
                // Store all CSS animations using Web Animations API
                window.__animationElements = [];

                document.querySelectorAll('*').forEach(function(el) {
                    var animations = el.getAnimations();
                    if (animations.length > 0) {
                        animations.forEach(function(anim) {
                            // Pause the animation at its current state
                            anim.pause();
                            window.__animationElements.push(anim);
                        });
                    }
                });

                console.log('Paused ' + window.__animationElements.length + ' animations');

                // Store animation start time for precise control
                window.__animationStartTime = performance.now();
            """)

            # Check how many animations were paused
            num_paused = driver.execute_script("return window.__animationElements ? window.__animationElements.length : 0;")
            self.log(f"Paused {num_paused} CSS animations for frame-by-frame control")

            # Capture frames
            self.log(f"=== FRAME CAPTURE ===")
            self.log(f"Total frames to capture: {total_frames}")
            self.log(f"Frame rate: {config.fps} FPS")
            self.log(f"Duration: {config.duration}s")
            self.log(f"Time between frames: {frame_time_s:.4f}s")
            self.update_progress(0.3, "Capturing frames...")

            for frame_num in range(total_frames):
                frame_progress = 0.3 + (0.4 * (frame_num + 1) / total_frames)
                self.update_progress(frame_progress, f"Frame {frame_num + 1}/{total_frames}")

                if self.cancelled:
                    driver.quit()
                    return None

                # Set animation time for this frame
                # Apply animation speed multiplier (e.g., 0.85 = 15% slower)
                elapsed_ms = frame_num * frame_time_s * config.animation_speed * 1000

                if frame_num % 30 == 0:  # Log every 30 frames
                    elapsed_time = frame_num * frame_time_s * config.animation_speed
                    self.log(f"Animation at {elapsed_time:.2f}s (frame {frame_num}, speed: {config.animation_speed}x)")

                # Control animation timing precisely using Web Animations API
                driver.execute_script(f"""
                    var elapsedMs = {elapsed_ms};

                    // Update all paused CSS animations to exact time
                    if (window.__animationElements) {{
                        window.__animationElements.forEach(function(anim) {{
                            anim.currentTime = elapsedMs;
                        }});
                    }}

                    // Update time for JavaScript animations
                    if (typeof createjs !== 'undefined' && createjs.Ticker) {{
                        createjs.Ticker._tick();
                    }}

                    if (typeof gsap !== 'undefined' && gsap.globalTimeline) {{
                        gsap.ticker.tick();
                    }}

                    // Force reflow
                    document.body.offsetHeight;
                """)

                frame_path = os.path.join(frames_dir, f"frame_{frame_num:06d}.png")
                temp_screenshot = frame_path + ".tmp.png"

                # Take screenshot AFTER waiting
                if frame_num == 0 or frame_num % 10 == 0 or frame_num == total_frames - 1:
                    self.log(f"Capturing frame {frame_num + 1}/{total_frames}")
                driver.save_screenshot(temp_screenshot)

                # Save frames at TARGET resolution (proportionally scaled and centered)
                with Image.open(temp_screenshot) as img:
                    screenshot_w, screenshot_h = img.size

                    # Technical screenshot analysis on first frame
                    if frame_num == 0:
                        self.log(f"=== SCREENSHOT ANALYSIS ===")
                        self.log(f"Screenshot size: {screenshot_w}x{screenshot_h}")
                        self.log(f"Expected size (target frame): {target_width}x{target_height}")

                        if abs(screenshot_w - target_width) < 10 and abs(screenshot_h - target_height) < 10:
                            self.log(f"Action: PROPORTIONAL SCALING SUCCESS!")
                            self.log(f"Screenshot matches target frame")
                            self.log(f"Content is scaled {scale_factor:.2f}x and centered")
                            # Save as-is, already at target dimensions with padding
                            img.save(frame_path)
                        else:
                            self.log(f"WARNING: Screenshot size mismatch")
                            self.log(f"Expected: {target_width}x{target_height}, Got: {screenshot_w}x{screenshot_h}")
                            # Resize to target if needed
                            if screenshot_w != target_width or screenshot_h != target_height:
                                resized = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                                resized.save(frame_path)
                            else:
                                img.save(frame_path)
                    else:
                        # For subsequent frames, just save as-is
                        img.save(frame_path)

                    # REQUIREMENT #7: Output debug frame 'frame_fixed.png'
                    if frame_num == 0:
                        debug_frame = os.path.join(output_dir, "frame_fixed.png")
                        with Image.open(frame_path) as fixed_img:
                            fixed_img.save(debug_frame)
                            final_w, final_h = fixed_img.size
                            self.log(f"=== DEBUG FRAME OUTPUT ===")
                            self.log(f"Saved: frame_fixed.png")
                            self.log(f"Frame dimensions: {final_w}x{final_h}")
                            self.log(f"Content: {config.width}x{config.height} scaled {scale_factor:.2f}x = {scaled_width}x{scaled_height}")
                            self.log(f"Padding: {pad_x}px H, {pad_y}px V (background: {bg_color_hex})")

                os.unlink(temp_screenshot)

                if frame_num == 0 or frame_num % 10 == 0 or frame_num == total_frames - 1:
                    self.log(f"Frame {frame_num + 1} saved: {os.path.basename(frame_path)}")

            self.log(f"=== FRAME CAPTURE COMPLETE ===")
            self.log(f"Total frames captured: {total_frames}")
            self.log(f"Frames directory: {frames_dir}")

            driver.quit()
            self.log("Browser closed")

        except Exception as e:
            self.log(f"=== RENDERING ERROR ===")
            self.log(f"Exception type: {type(e).__name__}")
            self.log(f"Exception message: {str(e)}")
            import traceback
            self.log(f"Traceback:\n{traceback.format_exc()}")
            try:
                driver.quit()
                self.log("Browser closed after error")
            except Exception:
                self.log("Failed to close browser")
            return None, None

        # Frames are already at target dimensions with proportional scaling and padding
        # No additional FFmpeg processing needed
        self.log(f"=== FRAME RENDERING COMPLETE ===")
        self.log(f"Frames ready at target dimensions: {target_width}x{target_height}")
        self.log(f"Proportional scaling applied: {scale_factor:.2f}x (no stretching)")
        self.log(f"No FFmpeg padding needed - frames are ready for encoding")
        return frames_dir, None

    def encode_video(self, frames_dir: str, output_path: str, config: VideoConfig, padding_info: dict = None) -> bool:
        """Encode frames to video using FFmpeg

        Args:
            frames_dir: Directory containing frames
            output_path: Output video file path
            config: Video configuration
            padding_info: Optional dict with padding info for format conversion
                         {'bg_color': '#rrggbb', 'source_width': int, 'source_height': int,
                          'target_width': int, 'target_height': int}
        """
        self.log(f"=== VIDEO ENCODING ===")
        self.log(f"Frames directory: {frames_dir}")
        self.log(f"Output path: {output_path}")
        if padding_info:
            self.log(f"Format conversion: {padding_info['source_width']}x{padding_info['source_height']} → {padding_info['target_width']}x{padding_info['target_height']}")
            self.log(f"Padding color: {padding_info['bg_color']}")

        input_pattern = os.path.join(frames_dir, "frame_%06d.png")
        self.log(f"Input pattern: {input_pattern}")

        # Check if frames exist first
        frame_files = sorted([f for f in os.listdir(frames_dir) if f.endswith('.png')])
        self.log(f"Checking for frames in: {frames_dir}")
        self.log(f"Found {len(frame_files)} PNG files")

        if not frame_files:
            self.log("ERROR: No frames found to encode!")
            return False

        self.log(f"Frame files: {frame_files[0]} ... {frame_files[-1]}")
        self.update_progress(0.75, "Encoding video...")

        # Get frame dimensions and build FFmpeg filter
        from PIL import Image
        first_frame_path = os.path.join(frames_dir, frame_files[0])
        self.log(f"=== DIMENSION CHECK ===")
        self.log(f"Reading first frame: {frame_files[0]}")
        needs_filter = False
        video_filter = ""

        try:
            with Image.open(first_frame_path) as img:
                frame_width, frame_height = img.size
                self.log(f"Captured frame size: {frame_width}x{frame_height}")

                # Build filter chain based on whether we need padding
                filter_parts = []

                if padding_info:
                    # Frames are at native size, need to pad to target format
                    src_w = padding_info['source_width']
                    src_h = padding_info['source_height']
                    tgt_w = padding_info['target_width']
                    tgt_h = padding_info['target_height']
                    bg_color = padding_info['bg_color'].lstrip('#')  # Remove # for FFmpeg

                    # Calculate padding to center content
                    # scale to fit (preserving aspect ratio)
                    scale_x = tgt_w / src_w
                    scale_y = tgt_h / src_h
                    scale = min(scale_x, scale_y)

                    scaled_w = int(src_w * scale)
                    scaled_h = int(src_h * scale)

                    # Ensure even dimensions for H.264
                    scaled_w = scaled_w if scaled_w % 2 == 0 else scaled_w - 1
                    scaled_h = scaled_h if scaled_h % 2 == 0 else scaled_h - 1
                    tgt_w = tgt_w if tgt_w % 2 == 0 else tgt_w - 1
                    tgt_h = tgt_h if tgt_h % 2 == 0 else tgt_h - 1

                    # Calculate padding
                    pad_x = (tgt_w - scaled_w) // 2
                    pad_y = (tgt_h - scaled_h) // 2

                    self.log(f"FFmpeg padding strategy:")
                    self.log(f"  1. Scale: {src_w}x{src_h} → {scaled_w}x{scaled_h} (scale factor: {scale:.2f}x)")
                    self.log(f"  2. Pad: Add {pad_x}px left/right, {pad_y}px top/bottom")
                    self.log(f"  3. Final: {tgt_w}x{tgt_h} with color {bg_color}")

                    # Build filter: scale, sharpen, then pad
                    filter_parts.append(f"scale={scaled_w}:{scaled_h}:flags=lanczos")
                    filter_parts.append("unsharp=5:5:1.0:5:5:0.0")
                    filter_parts.append(f"pad={tgt_w}:{tgt_h}:{pad_x}:{pad_y}:color=0x{bg_color}")

                    video_filter = f"-vf {','.join(filter_parts)}"
                    needs_filter = True

                else:
                    # No format change, just ensure even dimensions and sharpen
                    target_width = frame_width if frame_width % 2 == 0 else frame_width - 1
                    target_height = frame_height if frame_height % 2 == 0 else frame_height - 1

                    if frame_width != target_width or frame_height != target_height:
                        video_filter = f"-vf scale={target_width}:{target_height}:flags=lanczos,unsharp=5:5:1.0:5:5:0.0"
                        self.log(f"Adjusting for even dimensions: {frame_width}x{frame_height} → {target_width}x{target_height}")
                    else:
                        video_filter = "-vf unsharp=5:5:1.0:5:5:0.0"
                        self.log(f"Frames at native size ({frame_width}x{frame_height}) - adding sharpen only")
                    needs_filter = True

        except Exception as e:
            self.log(f"ERROR: Could not read frame: {e}")
            # Fallback
            if padding_info:
                tgt_w = padding_info['target_width']
                tgt_h = padding_info['target_height']
            else:
                tgt_w = config.width
                tgt_h = config.height
            tgt_w = tgt_w if tgt_w % 2 == 0 else tgt_w - 1
            tgt_h = tgt_h if tgt_h % 2 == 0 else tgt_h - 1
            video_filter = f"-vf scale={tgt_w}:{tgt_h}:flags=lanczos,unsharp=5:5:1.0:5:5:0.0"
            needs_filter = True
            self.log(f"Using fallback dimensions: {tgt_w}x{tgt_h}")

        # Build FFmpeg command with maximum compatibility
        self.log(f"=== BUILDING FFMPEG COMMAND ===")
        self.log(f"Codec: {config.codec}")
        self.log(f"FPS: {config.fps}")
        self.log(f"CRF: {config.crf}")
        self.log(f"Preset: {config.preset}")
        self.log(f"Bitrate: {config.bitrate}")

        ffmpeg_cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-framerate", str(config.fps),
            "-i", input_pattern,
        ]

        # Only add video filter if needed
        if needs_filter:
            ffmpeg_cmd.extend(video_filter.split())
            self.log(f"Added video filter to command: {video_filter}")

        ffmpeg_cmd.extend([
            "-c:v", config.codec,
            "-pix_fmt", "yuv420p",
        ])

        # Add codec-specific settings - keep it SIMPLE for cloud compatibility
        if config.codec in ["libx264", "libx265"]:
            # Use CRF for quality control
            ffmpeg_cmd.extend(["-crf", str(config.crf)])
            ffmpeg_cmd.extend(["-preset", config.preset])
            self.log(f"Using preset: {config.preset}, CRF: {config.crf}")
        elif config.codec == "libvpx-vp9":
            ffmpeg_cmd.extend(["-b:v", config.bitrate])
            ffmpeg_cmd.extend(["-crf", str(config.crf)])
            self.log(f"Using VP9 codec with bitrate and CRF")
        else:
            # For other codecs, use simple bitrate
            ffmpeg_cmd.extend(["-b:v", config.bitrate])
            self.log(f"Using simple bitrate for codec: {config.codec}")

        # Add universal compatibility flags
        ffmpeg_cmd.extend(["-movflags", "+faststart"])
        self.log(f"Added faststart flag for web compatibility")

        # Add output path
        ffmpeg_cmd.append(output_path)

        try:
            # Log FFmpeg command
            ffmpeg_command_str = " ".join(ffmpeg_cmd)
            self.log(f"=== FFMPEG EXECUTION ===")
            self.log(f"Command: {ffmpeg_command_str}")
            self.log("Starting FFmpeg process...")

            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            self.log(f"FFmpeg process started (PID: {process.pid})")
            self.log("Waiting for FFmpeg to complete...")

            # Poll process and check for cancellation
            while process.poll() is None:
                if self.cancelled:
                    self.log("Cancellation detected, terminating FFmpeg process...")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.log("FFmpeg did not terminate, forcing kill...")
                        process.kill()
                    self.log("FFmpeg process terminated by user cancellation")
                    return False
                time.sleep(0.1)

            # Capture output
            stdout, stderr = process.communicate()

            self.log(f"FFmpeg process finished (exit code: {process.returncode})")

            if process.returncode == 0:
                self.log(f"=== FFMPEG OUTPUT ===")
                for line in stderr.strip().split('\n'):
                    if line.strip():
                        self.log(line)
                self.log("=== ENCODING SUCCESS ===")
                self.log("Video encoding complete (exit code 0)")
                return True
            else:
                # Log detailed error
                self.log(f"=== FFMPEG ERROR ===")
                self.log(f"Exit code: {process.returncode}")
                self.log(f"STDERR output:")
                for line in stderr.strip().split('\n'):
                    if line.strip():
                        self.log(line)

                # Try fallback with minimal parameters
                self.log("=== ATTEMPTING FALLBACK ENCODING ===")
                self.log("Primary encoding failed, trying fallback with minimal parameters...")

                # Get actual frame dimensions from first frame
                try:
                    from PIL import Image
                    first_frame_path = os.path.join(frames_dir, frame_files[0])
                    with Image.open(first_frame_path) as img:
                        fw, fh = img.size
                        # Ensure even dimensions
                        fw = fw if fw % 2 == 0 else fw - 1
                        fh = fh if fh % 2 == 0 else fh - 1
                        self.log(f"Fallback dimensions from frame: {fw}x{fh}")
                except Exception as e:
                    fw, fh = 1280, 720  # Safe default
                    self.log(f"Could not read frame for fallback: {e}")
                    self.log(f"Using safe default: {fw}x{fh}")

                fallback_fps = min(config.fps, 30)
                self.log(f"Fallback FPS: {fallback_fps} (capped at 30)")

                fallback_cmd = [
                    "ffmpeg", "-y",
                    "-framerate", str(fallback_fps),
                    "-i", input_pattern,
                    "-vf", f"scale={fw}:{fh}:flags=lanczos,unsharp=5:5:1.0:5:5:0.0",
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-profile:v", "baseline",
                    "-level", "3.0",
                    "-r", str(fallback_fps),
                    output_path
                ]

                fallback_cmd_str = " ".join(fallback_cmd)
                self.log(f"Fallback command: {fallback_cmd_str}")
                self.log("Starting fallback FFmpeg process...")

                fallback_process = subprocess.Popen(
                    fallback_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )

                self.log(f"Fallback process started (PID: {fallback_process.pid})")
                fallback_stdout, fallback_stderr = fallback_process.communicate()
                self.log(f"Fallback process finished (exit code: {fallback_process.returncode})")

                if fallback_process.returncode == 0:
                    self.log("=== FALLBACK SUCCESS ===")
                    self.log("Fallback encoding succeeded using baseline profile")
                    for line in fallback_stderr.strip().split('\n'):
                        if line.strip():
                            self.log(line)
                    return True
                else:
                    self.log("=== FALLBACK FAILED ===")
                    self.log(f"Fallback exit code: {fallback_process.returncode}")
                    self.log("Fallback STDERR:")
                    for line in fallback_stderr.strip().split('\n'):
                        if line.strip():
                            self.log(line)
                    return False

        except FileNotFoundError:
            self.log("=== FFMPEG NOT FOUND ===")
            self.log("FileNotFoundError: FFmpeg executable not found in PATH")
            self.log("Please install FFmpeg or check packages.txt on Streamlit Cloud")
            return False
        except Exception as e:
            self.log("=== ENCODING EXCEPTION ===")
            self.log(f"Exception type: {type(e).__name__}")
            self.log(f"Exception message: {str(e)}")
            import traceback
            self.log(f"Traceback:\n{traceback.format_exc()}")
            return False

    def convert(self, zip_path: str, output_path: str, config: VideoConfig) -> bool:
        """Main conversion pipeline"""
        self.log("=== CONVERSION PIPELINE START ===")
        self.log(f"Input ZIP: {zip_path}")
        self.log(f"Output video: {output_path}")

        temp_dir = tempfile.mkdtemp(prefix="html5_to_video_")
        self.log(f"Created temp directory: {temp_dir}")

        try:
            self.log("=== STEP 1: EXTRACT ZIP ===")
            html_path = self.extract_zip(zip_path, temp_dir)
            if not html_path:
                self.log("ERROR: ZIP extraction failed")
                return False
            self.log(f"ZIP extraction successful: {html_path}")

            self.log("=== STEP 2: RENDER HTML TO FRAMES ===")
            frames_dir, padding_info = self.render_html_to_frames(html_path, temp_dir, config)
            if not frames_dir:
                self.log("ERROR: Frame rendering failed")
                return False
            self.log(f"Frame rendering successful: {frames_dir}")

            self.log("=== STEP 3: ENCODE VIDEO ===")
            success = self.encode_video(frames_dir, output_path, config, padding_info)

            if success:
                file_size = os.path.getsize(output_path) / (1024 * 1024)
                self.log(f"=== CONVERSION COMPLETE ===")
                self.log(f"Output video: {output_path}")
                self.log(f"File size: {file_size:.2f} MB")
                self.log(f"Total conversion time: {self._get_elapsed_time()}")
            else:
                self.log("ERROR: Video encoding failed")

            return success

        except Exception as e:
            self.log("=== CONVERSION EXCEPTION ===")
            self.log(f"Exception type: {type(e).__name__}")
            self.log(f"Exception message: {str(e)}")
            import traceback
            self.log(f"Traceback:\n{traceback.format_exc()}")
            return False
        finally:
            try:
                self.log("=== CLEANUP ===")
                self.log(f"Removing temp directory: {temp_dir}")
                shutil.rmtree(temp_dir)
                self.log("Cleanup complete")
            except Exception as cleanup_error:
                self.log(f"Cleanup error: {cleanup_error}")


def main():
    # Page config
    st.set_page_config(
        page_title="HTML5 to Video Converter",
        page_icon="🎥",  # Using simpler emoji that's more widely supported
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS - Dark Mode with Orange Theme
    st.markdown("""
        <style>
        /* Dark theme */
        .stApp {
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        }

        /* Headers */
        h1, h2, h3 {
            color: #ff8c42 !important;
        }

        /* Main title */
        .main-title {
            background: linear-gradient(135deg, #ff6b35 0%, #ff8c42 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 48px;
            font-weight: 800;
            text-align: center;
            margin-bottom: 10px;
        }

        .subtitle {
            color: #999;
            text-align: center;
            margin-bottom: 30px;
            font-size: 16px;
        }

        /* File uploader */
        .stFileUploader {
            background: #2d2d2d;
            border: 2px dashed #ff8c42;
            border-radius: 12px;
            padding: 20px;
        }

        /* Buttons */
        .stButton>button {
            background: linear-gradient(135deg, #ff6b35 0%, #ff8c42 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 30px;
            font-weight: 600;
            font-size: 16px;
            width: 100%;
        }

        .stButton>button:hover {
            background: linear-gradient(135deg, #ff5722 0%, #ff7731 100%);
            box-shadow: 0 4px 12px rgba(255, 107, 53, 0.4);
        }

        /* Info boxes */
        .stAlert {
            background: #2d2d2d;
            color: #fff;
            border-left: 4px solid #ff8c42;
        }

        /* Expander */
        .streamlit-expanderHeader {
            background: #2d2d2d;
            color: #ff8c42 !important;
            border-radius: 8px;
        }

        /* Sidebar */
        .css-1d391kg, [data-testid="stSidebar"] {
            background: #1a1a1a;
        }

        /* Input fields */
        .stNumberInput input, .stSelectbox select {
            background: #2d2d2d;
            color: #fff;
            border: 1px solid #ff8c42;
            border-radius: 6px;
        }

        /* Progress bar */
        .stProgress > div > div {
            background: linear-gradient(135deg, #ff6b35 0%, #ff8c42 100%);
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }

        .stTabs [data-baseweb="tab"] {
            background: #2d2d2d;
            color: #ff8c42;
            border-radius: 8px 8px 0 0;
        }

        .stTabs [aria-selected="true"] {
            background: #ff8c42;
            color: #1a1a1a;
        }

        /* Success message */
        .success-box {
            background: linear-gradient(135deg, #2d5016 0%, #3d6b1f 100%);
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid #4caf50;
            margin: 20px 0;
        }

        /* Smaller video preview for sharper low-res content */
        .stVideo {
            max-width: 100% !important;
        }

        .stVideo video {
            max-height: 250px !important;
            height: auto !important;
            max-width: 100% !important;
            width: auto !important;
            object-fit: contain !important;
            image-rendering: crisp-edges !important;
            image-rendering: -moz-crisp-edges !important;
            image-rendering: pixelated !important;
        }

        /* Also target the video element directly */
        video {
            max-height: 250px !important;
        }

        /* Make expander more discrete */
        .streamlit-expanderHeader {
            font-size: 14px;
            opacity: 0.7;
        }

        .streamlit-expanderHeader:hover {
            opacity: 1;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<h1 class="main-title">HTML5 to Video Converter</h1>', unsafe_allow_html=True)

    # Two-column layout from the start
    left_col, right_col = st.columns([2, 1])

    # Left column: Upload and settings
    with left_col:
        # Upload section
        uploaded_file = st.file_uploader(
            "Upload HTML5 ZIP file",
            type=['zip'],
            help="ZIP file containing HTML, CSS, JS, images, and all assets"
        )

        # Simple settings toggle
        mode = st.radio(
            "Mode",
            ["Auto", "Manual"],
            horizontal=True,
            label_visibility="collapsed"
        )

        # Info about automatic format detection
        st.info("ℹ️ Output format is automatically detected (1080x1080 or 1080x1920) based on source aspect ratio")

        # Manual mode settings
        if mode == "Manual":
            st.markdown("**Manual Settings**")
            col1, col2 = st.columns(2)
            with col1:
                width = st.number_input("Width", 100, 3840, 1920)  # Cap at 4K
                fps = st.number_input("FPS", 1, 60, 60)  # Cap at 60fps
            with col2:
                height = st.number_input("Height", 100, 2160, 1080)  # Cap at 4K
                duration = st.number_input("Duration", 1, 300, 10)  # Cap at 5 minutes

            # Animation speed control
            st.markdown("**Animation Speed**")
            animation_speed = st.slider(
                "Animation playback speed",
                min_value=0.5,
                max_value=1.5,
                value=0.85,
                step=0.05,
                help="Adjust animation playback speed. 0.85 = 15% slower (recommended), 1.0 = normal speed, 1.5 = 50% faster"
            )

            # Validate total computational load
            total_frames = fps * duration
            total_pixels = width * height * total_frames

            # Max: 4K @ 60fps for 60 seconds = 497,664,000 pixels
            max_pixels = 3840 * 2160 * 60 * 60
            if total_pixels > max_pixels:
                st.error("❌ Configuration too demanding")
                st.info(f"Total processing load: {total_pixels:,} pixel-frames. Maximum: {max_pixels:,}. Try reducing resolution, FPS, or duration.")
                st.stop()

    # Right column: Preview area (placeholder initially)
    with right_col:
        preview_container = st.container()
        with preview_container:
            st.markdown("### Preview")
            preview_placeholder = st.empty()
            preview_placeholder.info("Upload a file to see the preview here")
            download_placeholder = st.empty()

    # Continue with left column for conversion process
    with left_col:
        if uploaded_file:
            # Validate file
            if not uploaded_file.name.lower().endswith('.zip'):
                st.error("❌ Please upload a ZIP file")
                st.info("Your HTML5 content should be packaged as a .zip file")
                st.stop()

            # Check file size (50MB limit)
            max_size = 50 * 1024 * 1024  # 50MB
            if uploaded_file.size > max_size:
                st.error(f"❌ File too large ({uploaded_file.size / 1024 / 1024:.1f} MB)")
                st.info("Maximum file size: 50 MB")
                st.stop()

            # Save uploaded file
            temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
            temp_zip.write(uploaded_file.read())
            temp_zip.close()

            # Auto-detect if in auto mode
            if mode == "Auto":
                with st.spinner("Analyzing HTML5 content..."):
                    temp_extract = tempfile.mkdtemp()
                    with zipfile.ZipFile(temp_zip.name, 'r') as zip_ref:
                        zip_ref.extractall(temp_extract)

                    html_files = list(Path(temp_extract).rglob("*.html"))
                    if html_files:
                        main_html = None
                        for html_file in html_files:
                            if html_file.name.lower() in ['index.html', 'index.htm']:
                                main_html = html_file
                                break
                        if not main_html:
                            main_html = html_files[0]

                        analyzer = HTML5Analyzer()
                        detected = analyzer.analyze_html(str(main_html))

                        width = detected['width']
                        height = detected['height']
                        duration = detected['duration']
                        fps = detected['fps']

                        st.write("**Auto-detected settings:**")
                        col1, col2, col3, col4, col5 = st.columns(5)
                        col1.metric("Resolution", f"{width}x{height}")
                        col2.metric("FPS", fps)
                        col3.metric("Duration", f"{duration}s")
                        col4.metric("Quality", "High")
                        col5.metric("Anim Speed", "0.85x")

                        # Detect and show output format
                        from app import FormatCSS
                        output_width, output_height, format_name = FormatCSS.detect_best_format(width, height)
                        st.info(f"📐 **Output Format:** {format_name} - Your content will be automatically fitted to {output_width}x{output_height} with aspect ratio preserved")

                        # Use optimal settings for high quality (compatible with st.video)
                        codec = "libx264"
                        preset = "slow"
                        crf = 18  # High quality (compatible with web players)
                        bitrate = "10M"
                        animation_speed = 0.85  # Default: 15% slower for better visibility

                    else:
                        st.warning("No HTML files found, using defaults")
                        width, height, fps, duration = 1920, 1080, 60, 10
                        codec, preset, crf, bitrate = "libx264", "slow", 18, "10M"
                        animation_speed = 0.85  # Default: 15% slower for better visibility

                    shutil.rmtree(temp_extract)

            # Convert button
            if st.button("Convert to Video", use_container_width=True):
                output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                output_file.close()

                config = VideoConfig(
                    width=width,
                    height=height,
                    fps=fps,
                    duration=duration,
                    codec=codec,
                    bitrate=bitrate,
                    preset=preset,
                    crf=crf,
                    animation_speed=animation_speed
                )

                # Simple progress bar and status
                progress_bar = st.progress(0)
                status_text = st.empty()

                # Progress callback to update simple indicators
                def update_progress(value, message=None):
                    progress_bar.progress(value)
                    if message:
                        status_text.text(message)

                # Run conversion with error handling and cleanup
                converter = HTML5ToVideoConverter(progress_callback=update_progress)
                try:
                    success = converter.convert(temp_zip.name, output_file.name, config)
                except FileNotFoundError as e:
                    if "chrome" in str(e).lower() or "chromium" in str(e).lower():
                        st.error("❌ Browser not found. Please install Chrome or Chromium.")
                    elif "ffmpeg" in str(e).lower():
                        st.error("❌ FFmpeg not found. Please install FFmpeg.")
                    else:
                        st.error(f"❌ File not found: {e}")
                    st.info("💡 Check 'Debug Details' below for more information")
                    success = False
                except Exception as e:
                    st.error(f"❌ Conversion failed: {str(e)}")
                    st.info("💡 Check 'Debug Details' below for more information")
                    success = False
                finally:
                    # Always cleanup temp ZIP file
                    try:
                        if os.path.exists(temp_zip.name):
                            os.unlink(temp_zip.name)
                    except Exception:
                        pass

                # Complete
                progress_bar.progress(1.0)
                if success:
                    status_text.success("Complete")
                else:
                    status_text.empty()
                    # Cleanup output file on failure
                    try:
                        if os.path.exists(output_file.name):
                            os.unlink(output_file.name)
                    except Exception:
                        pass

                # Show terminal-style debug output (complete log)
                with st.expander("Debug Details", expanded=False):
                    debug_output = converter.get_debug_output()
                    st.code(debug_output, language="text")
                    st.caption("↑ Complete process log (copy entire log)")

                if success and os.path.exists(output_file.name):
                    # Read video bytes
                    with open(output_file.name, 'rb') as f:
                        video_bytes = f.read()

                    # Show video preview
                    preview_placeholder.video(video_bytes)

                    # Add download button
                    download_placeholder.download_button(
                        label="Download Video",
                        data=video_bytes,
                        file_name="converted_video.mp4",
                        mime="video/mp4",
                        use_container_width=True
                    )

                    # Cleanup output file (video already in memory as video_bytes)
                    try:
                        os.unlink(output_file.name)
                    except Exception:
                        pass



if __name__ == "__main__":
    main()
