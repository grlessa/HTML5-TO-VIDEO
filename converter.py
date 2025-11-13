"""
Main HTML5 to Video conversion engine.
"""
import os
import tempfile
import zipfile
import shutil
import subprocess
import time
import traceback
from typing import Optional, Callable
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from config import (
    VideoConfig,
    PAGE_LOAD_TIMEOUT,
    SCRIPT_TIMEOUT,
    PAGE_SETTLE_DELAY,
    ANIMATION_INIT_DELAY,
    ANIMATION_PAUSE_DELAY,
    VIEWPORT_CORRECTION_DELAY,
    FALLBACK_FPS,
    FALLBACK_PROFILE,
    FALLBACK_LEVEL,
    DEFAULT_PIXEL_FORMAT,
)
from formatters import SocialMediaFormatter, AspectRatioCalculator
from utils import (
    ConversionLogger,
    rgb_to_hex,
    ensure_even_dimension,
    find_html_file,
    validate_zip_security,
    get_browser_binary_path,
    format_file_size,
)


class HTML5ToVideoConverter:
    """
    Converts HTML5 content to video files.
    
    This is the main conversion engine that orchestrates:
    1. ZIP extraction with security validation
    2. HTML rendering in headless browser
    3. Frame-by-frame animation capture
    4. Video encoding with FFmpeg
    
    The converter supports automatic format detection and conversion
    for social media platforms (square/vertical).
    """
    
    def __init__(self, progress_callback: Optional[Callable[[float, str], None]] = None):
        """
        Initialize converter with optional progress callback.
        
        Args:
            progress_callback: Optional function(progress: float, message: str)
                              for reporting progress (0.0 to 1.0)
        """
        self.cancelled = False
        self.progress_callback = progress_callback
        self.logger = ConversionLogger()
    
    def update_progress(self, value: float, message: Optional[str] = None):
        """Update progress via callback if provided."""
        if self.progress_callback:
            self.progress_callback(value, message)
    
    def log(self, message: str) -> str:
        """Add message to debug log with timestamp."""
        return self.logger.log(message)
    
    def get_debug_log(self) -> str:
        """Get complete debug log as text."""
        return self.logger.get_log_text()
    
    # ==========================================================================
    # MAIN CONVERSION PIPELINE
    # ==========================================================================
    
    def convert(self, zip_path: str, output_path: str, config: VideoConfig) -> bool:
        """
        Main conversion pipeline: ZIP → HTML → Frames → Video.
        
        Args:
            zip_path: Path to HTML5 ZIP file
            output_path: Path for output MP4 file
            config: Video configuration parameters
            
        Returns:
            True if conversion succeeded, False otherwise
        """
        self.log("=== CONVERSION PIPELINE START ===")
        self.log(f"Input ZIP: {zip_path}")
        self.log(f"Output video: {output_path}")
        
        temp_dir = tempfile.mkdtemp(prefix="html5_to_video_")
        self.log(f"Created temp directory: {temp_dir}")
        
        try:
            # Step 1: Extract and validate ZIP
            self.log("=== STEP 1: EXTRACT ZIP ===")
            html_path = self._extract_zip(zip_path, temp_dir)
            if not html_path:
                self.log("ERROR: ZIP extraction failed")
                return False
            self.log(f"ZIP extraction successful: {html_path}")
            
            # Step 2: Render HTML to frames
            self.log("=== STEP 2: RENDER HTML TO FRAMES ===")
            frames_dir = self._render_html_to_frames(html_path, temp_dir, config)
            if not frames_dir:
                self.log("ERROR: Frame rendering failed")
                return False
            self.log(f"Frame rendering successful: {frames_dir}")
            
            # Step 3: Encode video from frames
            self.log("=== STEP 3: ENCODE VIDEO ===")
            success = self._encode_video(frames_dir, output_path, config)
            
            if success:
                file_size = os.path.getsize(output_path)
                self.log(f"=== CONVERSION COMPLETE ===")
                self.log(f"Output video: {output_path}")
                self.log(f"File size: {format_file_size(file_size)}")
                self.log(f"Total conversion time: {self.logger.get_elapsed_time()}")
            else:
                self.log("ERROR: Video encoding failed")
            
            return success
            
        except Exception as e:
            self.log("=== CONVERSION EXCEPTION ===")
            self.log(f"Exception type: {type(e).__name__}")
            self.log(f"Exception message: {str(e)}")
            self.log(f"Traceback:\n{traceback.format_exc()}")
            return False
            
        finally:
            # Always cleanup temp directory
            try:
                self.log("=== CLEANUP ===")
                self.log(f"Removing temp directory: {temp_dir}")
                shutil.rmtree(temp_dir)
                self.log("Cleanup complete")
            except Exception as cleanup_error:
                self.log(f"Cleanup error: {cleanup_error}")
    
    # ==========================================================================
    # STEP 1: ZIP EXTRACTION
    # ==========================================================================
    
    def _extract_zip(self, zip_path: str, extract_dir: str) -> Optional[str]:
        """
        Extract ZIP and find main HTML file with security validation.
        
        Performs security checks for:
        - Empty ZIPs
        - ZIP bombs (excessive files/size)
        - Path traversal attacks
        
        Args:
            zip_path: Path to ZIP file
            extract_dir: Directory to extract into
            
        Returns:
            Path to main HTML file, or None if extraction fails
        """
        self.update_progress(0.1, "Extracting...")
        self.log(f"=== ZIP EXTRACTION ===")
        self.log(f"ZIP path: {zip_path}")
        self.log(f"Extract to: {extract_dir}")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Security validation
                validate_zip_security(zip_ref)
                
                files = zip_ref.namelist()
                total_size = sum(info.file_size for info in zip_ref.infolist())
                
                self.log(f"ZIP contains {len(files)} files")
                self.log(f"Total uncompressed size: {format_file_size(total_size)}")
                
                # Extract all files
                zip_ref.extractall(extract_dir)
                self.log(f"Extracted all files successfully")
            
            # Find main HTML file
            html_file = find_html_file(extract_dir)
            self.log(f"Found HTML files, using: {html_file.name}")
            self.log(f"Absolute path: {html_file.absolute()}")
            
            return str(html_file.absolute())
            
        except Exception as e:
            self.log(f"ERROR during extraction: {e}")
            return None
    
    # ==========================================================================
    # STEP 2: HTML RENDERING TO FRAMES
    # ==========================================================================
    
    def _render_html_to_frames(
        self,
        html_path: str,
        output_dir: str,
        config: VideoConfig
    ) -> Optional[str]:
        """
        Render HTML to individual frame images.
        
        This complex process:
        1. Sets up headless browser
        2. Loads HTML with format conversion
        3. Triggers and controls animations
        4. Captures frames at precise intervals
        
        Args:
            html_path: Path to HTML file
            output_dir: Directory for output frames
            config: Video configuration
            
        Returns:
            Path to frames directory, or None if rendering fails
        """
        self.update_progress(0.2, "Loading browser...")
        
        frames_dir = os.path.join(output_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)
        
        # Calculate frame parameters
        total_frames = config.fps * config.duration
        frame_time_seconds = 1.0 / config.fps
        
        self.log(f"=== HTML5 TO VIDEO RENDERING ===")
        self.log(f"Source dimensions: {config.width}x{config.height}")
        
        # Determine target format
        target_width, target_height, format_name = self._get_target_format(config)
        
        self.log(f"Target format: {format_name}")
        self.log(f"Target dimensions: {target_width}x{target_height}")
        self.log(f"Total frames: {total_frames} ({config.fps} FPS × {config.duration}s)")
        self.log(f"Frame interval: {frame_time_seconds:.4f}s")
        
        # Calculate scaling parameters
        scale_factor, scaled_width, scaled_height, pad_x, pad_y = \
            self._calculate_scaling_params(
                config.width, config.height, target_width, target_height
            )
        
        self.log(f"Scale factor: {scale_factor:.2f}x (proportional)")
        self.log(f"Scaled content: {scaled_width}x{scaled_height}")
        self.log(f"Padding: {pad_x}px horizontal, {pad_y}px vertical")
        
        # Setup and launch browser
        driver = self._setup_browser(target_width, target_height)
        if not driver:
            return None
        
        try:
            # Load HTML page
            if not self._load_html_page(driver, html_path, target_width, target_height):
                driver.quit()
                return None
            
            # Apply format conversion if needed
            bg_color_hex = self._apply_format_conversion(
                driver, config, target_width, target_height,
                scale_factor, pad_x, pad_y
            )
            
            # Verify and correct viewport dimensions
            self._verify_and_correct_viewport(driver, target_width, target_height)
            
            # Setup animations
            self._setup_animations(driver)
            
            # Capture all frames
            success = self._capture_frames(
                driver, frames_dir, total_frames,
                frame_time_seconds, config,
                target_width, target_height,
                scale_factor, scaled_width, scaled_height,
                pad_x, pad_y, bg_color_hex, output_dir
            )
            
            self.log(f"=== FRAME CAPTURE COMPLETE ===")
            self.log(f"Total frames captured: {total_frames}")
            self.log(f"Frames directory: {frames_dir}")
            
            self._cleanup_browser(driver)
            
            return frames_dir if success else None
            
        except Exception as e:
            self.log(f"=== RENDERING ERROR ===")
            self.log(f"Exception: {type(e).__name__}: {str(e)}")
            self.log(f"Traceback:\n{traceback.format_exc()}")
            try:
                self._cleanup_browser(driver)
            except:
                pass
            return None
    
    def _get_target_format(self, config: VideoConfig) -> tuple[int, int, str]:
        """Get target output format based on configuration."""
        if config.target_format == "square":
            from config import SQUARE_FORMAT
            return SQUARE_FORMAT
        elif config.target_format == "vertical":
            from config import VERTICAL_FORMAT
            return VERTICAL_FORMAT
        else:  # auto
            return SocialMediaFormatter.detect_best_format(config.width, config.height)
    
    def _calculate_scaling_params(
        self,
        source_w: int,
        source_h: int,
        target_w: int,
        target_h: int
    ) -> tuple[float, int, int, int, int]:
        """
        Calculate scaling and padding parameters.
        
        Returns:
            (scale_factor, scaled_width, scaled_height, pad_x, pad_y)
        """
        scale_factor_w = target_w / source_w
        scale_factor_h = target_h / source_h
        scale_factor = min(scale_factor_w, scale_factor_h)  # Proportional scaling
        
        scaled_width = int(source_w * scale_factor)
        scaled_height = int(source_h * scale_factor)
        
        pad_x = (target_w - scaled_width) // 2
        pad_y = (target_h - scaled_height) // 2
        
        return scale_factor, scaled_width, scaled_height, pad_x, pad_y
    
    def _setup_browser(self, width: int, height: int) -> Optional[webdriver.Chrome]:
        """
        Setup and launch headless Chrome browser.
        
        Args:
            width: Window width
            height: Window height
            
        Returns:
            WebDriver instance or None if setup fails
        """
        self.log(f"=== BROWSER INITIALIZATION ===")
        
        # Create unique user data directory for this session
        # Use PID and timestamp to ensure uniqueness
        import random
        unique_id = f"{os.getpid()}_{int(time.time())}_{random.randint(1000, 9999)}"
        user_data_dir = tempfile.mkdtemp(prefix=f"chrome_user_data_{unique_id}_")
        self.log(f"Chrome user data dir: {user_data_dir}")
        
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--hide-scrollbars')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument(f'--window-size={width},{height}')
        chrome_options.add_argument('--force-device-scale-factor=1')
        chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
        
        # Additional isolation options
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-breakpad')
        chrome_options.add_argument('--disable-client-side-phishing-detection')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-hang-monitor')
        chrome_options.add_argument('--disable-popup-blocking')
        chrome_options.add_argument('--disable-prompt-on-repost')
        chrome_options.add_argument('--disable-sync')
        chrome_options.add_argument('--disable-translate')
        chrome_options.add_argument('--metrics-recording-only')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--safebrowsing-disable-auto-update')
        chrome_options.add_argument('--enable-automation')
        chrome_options.add_argument('--password-store=basic')
        chrome_options.add_argument('--use-mock-keychain')
        chrome_options.add_argument('--remote-debugging-port=0')  # Random port
        
        # Find browser binary
        browser_path = get_browser_binary_path()
        if browser_path:
            chrome_options.binary_location = browser_path
            self.log(f"Found browser: {browser_path}")
        else:
            self.log("WARNING: No browser binary found, using system default")
        
        try:
            self.log("Creating WebDriver instance...")
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
            driver.set_script_timeout(SCRIPT_TIMEOUT)
            self.log("WebDriver created successfully")
            
            # Store user data dir for cleanup
            driver._user_data_dir = user_data_dir
            
            return driver
        except Exception as e:
            self.log(f"ERROR: Failed to create WebDriver: {e}")
            # Cleanup user data dir on failure
            try:
                shutil.rmtree(user_data_dir, ignore_errors=True)
            except:
                pass
            return None
    
    def _cleanup_browser(self, driver: webdriver.Chrome):
        """
        Cleanup browser and its temporary user data directory.
        
        Args:
            driver: WebDriver instance to cleanup
        """
        try:
            # Get user data dir before quitting
            user_data_dir = getattr(driver, '_user_data_dir', None)
            
            # Quit the browser
            driver.quit()
            self.log("Browser closed")
            
            # Cleanup user data directory
            if user_data_dir and os.path.exists(user_data_dir):
                shutil.rmtree(user_data_dir, ignore_errors=True)
                self.log(f"Cleaned up Chrome user data dir")
        except Exception as e:
            self.log(f"Warning during browser cleanup: {e}")
    
    def _load_html_page(
        self,
        driver: webdriver.Chrome,
        html_path: str,
        width: int,
        height: int
    ) -> bool:
        """
        Load HTML page in browser.
        
        Args:
            driver: WebDriver instance
            html_path: Path to HTML file
            width: Window width
            height: Window height
            
        Returns:
            True if page loaded successfully
        """
        self.log(f"=== PAGE LOADING ===")
        driver.set_window_size(width, height)
        self.log(f"Set window size: {width}x{height}")
        
        file_url = f"file://{html_path}"
        self.log(f"Loading URL: {file_url}")
        
        try:
            driver.get(file_url)
            self.log(f"Page loaded successfully")
            return True
        except Exception as e:
            self.log(f"ERROR: Failed to load page: {e}")
            return False
    
    def _apply_format_conversion(
        self,
        driver: webdriver.Chrome,
        config: VideoConfig,
        target_width: int,
        target_height: int,
        scale_factor: float,
        pad_x: int,
        pad_y: int
    ) -> str:
        """
        Apply format conversion with proportional scaling.
        
        Returns:
            Background color in hex format
        """
        needs_format_change = (
            target_width != config.width or target_height != config.height
        )
        
        if not needs_format_change:
            self.log(f"=== STANDARD RENDERING ===")
            self.log(f"Using native dimensions: {config.width}x{config.height}")
            # Apply minimal CSS for clean rendering
            driver.execute_script("""
                document.documentElement.style.margin = '0';
                document.documentElement.style.padding = '0';
                document.documentElement.style.overflow = 'hidden';
                document.body.style.margin = '0';
                document.body.style.padding = '0';
                document.body.style.overflow = 'hidden';
            """)
            return "#000000"
        
        # High-resolution rendering with format conversion
        self.log(f"=== HIGH-RESOLUTION RENDERING SETUP ===")
        
        # Extract background color
        bg_color_hex = self._extract_background_color(driver)
        
        self.log(f"=== PROPORTIONAL SCALING STRATEGY ===")
        self.log(f"Browser viewport: {target_width}x{target_height} (target frame)")
        self.log(f"Source content: {config.width}x{config.height}")
        self.log(f"Proportional scale: {scale_factor:.3f}x (uniform)")
        self.log(f"Centering with padding: {pad_x}px H, {pad_y}px V")
        self.log(f"Background color: {bg_color_hex}")
        
        # Load and execute browser-side JavaScript
        from utils import load_javascript_file
        js_code = load_javascript_file("browser_scripts.js")
        driver.execute_script(js_code)
        
        # Apply proportional scaling
        driver.execute_script(
            f"applyProportionalScaling({target_width}, {target_height}, "
            f"{config.width}, {config.height}, {scale_factor}, "
            f"{pad_x}, {pad_y}, '{bg_color_hex}');"
        )
        
        self.log(f"Applied proportional scaling with forced viewport")
        
        return bg_color_hex
    
    def _extract_background_color(self, driver: webdriver.Chrome) -> str:
        """
        Extract predominant background color from page.
        
        Returns:
            Hex color string
        """
        try:
            from utils import load_javascript_file
            js_code = load_javascript_file("browser_scripts.js")
            driver.execute_script(js_code)
            
            bg_color_rgb = driver.execute_script("return getPredominantBackgroundColor();")
            bg_color_hex = rgb_to_hex(bg_color_rgb)
            
            self.log(f"Detected background color: {bg_color_rgb} → {bg_color_hex}")
            return bg_color_hex
        except Exception as e:
            self.log(f"Could not detect background color: {e}")
            return "#000000"
    
    def _verify_and_correct_viewport(
        self,
        driver: webdriver.Chrome,
        target_width: int,
        target_height: int
    ):
        """
        Verify viewport matches target and correct if needed.
        
        Chrome sometimes subtracts UI chrome from window size,
        so we may need to compensate.
        """
        time.sleep(PAGE_SETTLE_DELAY)
        
        actual_viewport_w = driver.execute_script("return window.innerWidth;")
        actual_viewport_h = driver.execute_script("return window.innerHeight;")
        
        self.log(f"=== DIMENSION VERIFICATION ===")
        self.log(f"Target viewport: {target_width}x{target_height}")
        self.log(f"Actual viewport: {actual_viewport_w}x{actual_viewport_h}")
        
        if actual_viewport_w != target_width or actual_viewport_h != target_height:
            self.log(f"WARNING: Viewport mismatch, correcting...")
            
            height_diff = target_height - actual_viewport_h
            width_diff = target_width - actual_viewport_w
            
            corrected_width = target_width + width_diff
            corrected_height = target_height + height_diff
            
            self.log(f"Resizing to: {corrected_width}x{corrected_height}")
            driver.set_window_size(corrected_width, corrected_height)
            
            time.sleep(VIEWPORT_CORRECTION_DELAY)
            
            new_viewport_w = driver.execute_script("return window.innerWidth;")
            new_viewport_h = driver.execute_script("return window.innerHeight;")
            
            if new_viewport_w == target_width and new_viewport_h == target_height:
                self.log(f"SUCCESS: Viewport corrected")
            else:
                self.log(f"WARNING: Viewport still mismatched: {new_viewport_w}x{new_viewport_h}")
    
    def _setup_animations(self, driver: webdriver.Chrome):
        """
        Trigger and prepare animations for frame-by-frame capture.
        """
        self.log(f"=== ANIMATION SETUP ===")
        self.log("Triggering animations...")
        
        # Load JavaScript functions
        from utils import load_javascript_file
        js_code = load_javascript_file("browser_scripts.js")
        driver.execute_script(js_code)
        
        # Trigger all animations
        driver.execute_script("triggerAnimations();")
        time.sleep(ANIMATION_INIT_DELAY)
        
        # Gather animation info
        animations_info = driver.execute_script("return gatherAnimationInfo();")
        self.log(f"CSS info: {animations_info['stylesheets']} stylesheets, "
                f"{len(animations_info['animations'])} keyframe animations")
        if animations_info['animations']:
            self.log(f"Keyframes: {', '.join(animations_info['animations'])}")
        self.log(f"Elements with animations: {animations_info['animated_elements']}")
        
        # Allow brief initialization then pause for control
        time.sleep(ANIMATION_PAUSE_DELAY)
        
        # Pause animations for frame-by-frame control
        num_paused = driver.execute_script("return pauseAnimationsForControl();")
        self.log(f"Paused {num_paused} animations for frame control")
    
    def _capture_frames(
        self,
        driver: webdriver.Chrome,
        frames_dir: str,
        total_frames: int,
        frame_time: float,
        config: VideoConfig,
        target_width: int,
        target_height: int,
        scale_factor: float,
        scaled_width: int,
        scaled_height: int,
        pad_x: int,
        pad_y: int,
        bg_color: str,
        output_dir: str
    ) -> bool:
        """
        Capture all animation frames.
        
        Returns:
            True if all frames captured successfully
        """
        self.log(f"=== FRAME CAPTURE ===")
        self.log(f"Capturing {total_frames} frames...")
        self.update_progress(0.3, "Capturing frames...")
        
        for frame_num in range(total_frames):
            # Update progress
            frame_progress = 0.3 + (0.4 * (frame_num + 1) / total_frames)
            self.update_progress(frame_progress, f"Frame {frame_num + 1}/{total_frames}")
            
            if self.cancelled:
                self.log("Capture cancelled by user")
                return False
            
            # Set animation time for this frame
            elapsed_ms = frame_num * frame_time * 1000
            driver.execute_script(f"setAnimationTime({elapsed_ms});")
            
            # Log progress periodically
            if frame_num % 30 == 0:
                self.log(f"Capturing frame {frame_num + 1}/{total_frames}")
            
            # Take screenshot
            frame_path = os.path.join(frames_dir, f"frame_{frame_num:06d}.png")
            temp_screenshot = frame_path + ".tmp.png"
            driver.save_screenshot(temp_screenshot)
            
            # Process screenshot
            self._process_frame(
                temp_screenshot, frame_path, frame_num,
                target_width, target_height,
                scale_factor, scaled_width, scaled_height,
                pad_x, pad_y, bg_color, output_dir
            )
            
            os.unlink(temp_screenshot)
        
        self.log(f"All {total_frames} frames captured")
        return True
    
    def _process_frame(
        self,
        temp_path: str,
        final_path: str,
        frame_num: int,
        target_width: int,
        target_height: int,
        scale_factor: float,
        scaled_width: int,
        scaled_height: int,
        pad_x: int,
        pad_y: int,
        bg_color: str,
        output_dir: str
    ):
        """Process and validate a captured frame."""
        with Image.open(temp_path) as img:
            screenshot_w, screenshot_h = img.size
            
            # Log first frame details
            if frame_num == 0:
                self.log(f"=== SCREENSHOT ANALYSIS ===")
                self.log(f"Screenshot size: {screenshot_w}x{screenshot_h}")
                self.log(f"Expected: {target_width}x{target_height}")
                
                # Check if dimensions match
                if abs(screenshot_w - target_width) < 10 and \
                   abs(screenshot_h - target_height) < 10:
                    self.log(f"SUCCESS: Screenshot matches target")
                else:
                    self.log(f"WARNING: Size mismatch, will resize")
            
            # Resize if needed
            if screenshot_w != target_width or screenshot_h != target_height:
                img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            # Save processed frame
            img.save(final_path)
            
            # Save first frame as debug preview
            if frame_num == 0:
                debug_path = os.path.join(output_dir, "frame_preview.png")
                img.save(debug_path)
                self.log(f"Saved preview: frame_preview.png")
    
    # ==========================================================================
    # STEP 3: VIDEO ENCODING
    # ==========================================================================
    
    def _encode_video(
        self,
        frames_dir: str,
        output_path: str,
        config: VideoConfig
    ) -> bool:
        """
        Encode frames to video using FFmpeg.
        
        Args:
            frames_dir: Directory containing frame images
            output_path: Output video file path
            config: Video configuration
            
        Returns:
            True if encoding succeeded
        """
        self.log(f"=== VIDEO ENCODING ===")
        self.log(f"Frames directory: {frames_dir}")
        self.log(f"Output path: {output_path}")
        self.update_progress(0.75, "Encoding video...")
        
        # Validate frames exist
        frame_files = sorted([f for f in os.listdir(frames_dir) if f.endswith('.png')])
        if not frame_files:
            self.log("ERROR: No frames found to encode!")
            return False
        
        self.log(f"Found {len(frame_files)} frames")
        
        # Build FFmpeg command
        ffmpeg_cmd = self._build_ffmpeg_command(
            frames_dir, output_path, config, frame_files[0]
        )
        
        if not ffmpeg_cmd:
            return False
        
        # Execute FFmpeg
        success = self._execute_ffmpeg(ffmpeg_cmd, output_path)
        
        # Try fallback if primary encoding fails
        if not success:
            self.log("=== ATTEMPTING FALLBACK ENCODING ===")
            fallback_cmd = self._build_fallback_command(frames_dir, output_path, config)
            success = self._execute_ffmpeg(fallback_cmd, output_path)
        
        return success
    
    def _build_ffmpeg_command(
        self,
        frames_dir: str,
        output_path: str,
        config: VideoConfig,
        first_frame: str
    ) -> Optional[list]:
        """
        Build FFmpeg command with optimal settings.
        
        Returns:
            FFmpeg command as list, or None if build fails
        """
        input_pattern = os.path.join(frames_dir, "frame_%06d.png")
        
        # Get frame dimensions
        try:
            first_frame_path = os.path.join(frames_dir, first_frame)
            with Image.open(first_frame_path) as img:
                frame_width, frame_height = img.size
                self.log(f"Frame dimensions: {frame_width}x{frame_height}")
        except Exception as e:
            self.log(f"ERROR: Could not read frame: {e}")
            return None
        
        # Ensure even dimensions
        target_width = ensure_even_dimension(frame_width)
        target_height = ensure_even_dimension(frame_height)
        
        # Calculate output FPS based on animation speed
        output_fps = config.fps * config.animation_speed
        self.log(f"Animation speed: {config.animation_speed}x")
        self.log(f"Input FPS: {config.fps}, Output FPS: {output_fps:.2f}")
        
        # Build command
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(config.fps),
            "-i", input_pattern,
        ]
        
        # Add video filter if dimensions need adjustment
        if frame_width != target_width or frame_height != target_height:
            from config import NORMAL_SHARPEN
            cmd.extend([
                "-vf",
                f"scale={target_width}:{target_height}:flags=lanczos,{NORMAL_SHARPEN}"
            ])
            self.log(f"Added scaling filter: {target_width}x{target_height}")
        
        # Add encoding settings
        cmd.extend([
            "-c:v", config.codec,
            "-pix_fmt", DEFAULT_PIXEL_FORMAT,
            "-r", str(output_fps),
        ])
        
        # Add codec-specific settings
        if config.codec in ["libx264", "libx265"]:
            cmd.extend(["-crf", str(config.crf), "-preset", config.preset])
        else:
            cmd.extend(["-b:v", config.bitrate])
        
        # Add web compatibility flags
        cmd.extend(["-movflags", "+faststart"])
        cmd.append(output_path)
        
        self.log(f"FFmpeg command: {' '.join(cmd)}")
        return cmd
    
    def _build_fallback_command(
        self,
        frames_dir: str,
        output_path: str,
        config: VideoConfig
    ) -> list:
        """Build fallback FFmpeg command with baseline profile."""
        input_pattern = os.path.join(frames_dir, "frame_%06d.png")
        
        self.log("Using fallback encoding with baseline profile")
        
        return [
            "ffmpeg", "-y",
            "-framerate", str(min(config.fps, FALLBACK_FPS)),
            "-i", input_pattern,
            "-c:v", "libx264",
            "-pix_fmt", DEFAULT_PIXEL_FORMAT,
            "-profile:v", FALLBACK_PROFILE,
            "-level", FALLBACK_LEVEL,
            "-r", str(min(config.fps, FALLBACK_FPS)),
            output_path
        ]
    
    def _execute_ffmpeg(self, cmd: list, output_path: str) -> bool:
        """
        Execute FFmpeg command and monitor progress.
        
        Returns:
            True if encoding succeeded
        """
        try:
            self.log("Starting FFmpeg process...")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            self.log(f"FFmpeg process started (PID: {process.pid})")
            
            # Monitor process
            while process.poll() is None:
                if self.cancelled:
                    self.log("Encoding cancelled, terminating FFmpeg...")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    return False
                time.sleep(0.1)
            
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                self.log("=== ENCODING SUCCESS ===")
                self.log(f"Video encoded successfully")
                return True
            else:
                self.log(f"=== ENCODING FAILED ===")
                self.log(f"Exit code: {process.returncode}")
                self.log(f"Error output: {stderr[-500:]}")  # Last 500 chars
                return False
                
        except FileNotFoundError:
            self.log("ERROR: FFmpeg not found in PATH")
            return False
        except Exception as e:
            self.log(f"ERROR during encoding: {e}")
            return False

