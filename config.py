"""
Configuration and constants for HTML5 to Video Converter
"""
from dataclasses import dataclass
from typing import Final

# ==============================================================================
# DIMENSION CONSTRAINTS
# ==============================================================================

MIN_DIMENSION: Final[int] = 100
MAX_WIDTH: Final[int] = 7680  # 8K width
MAX_HEIGHT: Final[int] = 4320  # 8K height

# ==============================================================================
# ANIMATION DETECTION THRESHOLDS
# ==============================================================================

HIGH_ANIMATION_THRESHOLD: Final[int] = 10  # >10 keywords = 60fps
MEDIUM_ANIMATION_THRESHOLD: Final[int] = 3  # 4-10 keywords = 30fps
# <4 keywords = 24fps

HIGH_FPS: Final[int] = 60
MEDIUM_FPS: Final[int] = 30
LOW_FPS: Final[int] = 24

# Animation keywords to search for in HTML
ANIMATION_KEYWORDS: Final[list[str]] = [
    'animation',
    'transition',
    'transform',
    'requestAnimationFrame'
]

# ==============================================================================
# DURATION CONSTRAINTS
# ==============================================================================

MAX_AUTO_DETECTED_DURATION: Final[int] = 20  # Seconds
DEFAULT_DURATION: Final[int] = 10  # Seconds
MAX_DURATION: Final[int] = 300  # 5 minutes

# ==============================================================================
# FILE CONSTRAINTS
# ==============================================================================

MAX_ZIP_FILE_SIZE: Final[int] = 50 * 1024 * 1024  # 50MB
MAX_UNCOMPRESSED_SIZE: Final[int] = 50 * 1024 * 1024  # 50MB
MAX_FILES_IN_ZIP: Final[int] = 1000

# ==============================================================================
# SOCIAL MEDIA FORMATS
# ==============================================================================

# Format definitions: (width, height, name)
SQUARE_FORMAT: Final[tuple[int, int, str]] = (1080, 1080, "1080x1080 (Square/Instagram)")
VERTICAL_FORMAT: Final[tuple[int, int, str]] = (1080, 1920, "1080x1920 (Vertical/Stories)")

SQUARE_ASPECT_RATIO: Final[float] = 1.0  # 1:1
VERTICAL_ASPECT_RATIO: Final[float] = 9.0 / 16.0  # 9:16

# ==============================================================================
# VIDEO ENCODING DEFAULTS
# ==============================================================================

DEFAULT_CODEC: Final[str] = "libx264"
DEFAULT_PRESET: Final[str] = "slow"
DEFAULT_CRF: Final[int] = 18  # High quality
DEFAULT_BITRATE: Final[str] = "10M"
DEFAULT_ANIMATION_SPEED: Final[float] = 1.0  # Normal speed
DEFAULT_PIXEL_FORMAT: Final[str] = "yuv420p"

# Fallback encoding settings
FALLBACK_FPS: Final[int] = 30
FALLBACK_PROFILE: Final[str] = "baseline"
FALLBACK_LEVEL: Final[str] = "3.0"

# ==============================================================================
# BROWSER CONFIGURATION
# ==============================================================================

# Browser binary paths (checked in order)
# Note: Comet does not support headless mode reliably, so prefer Chrome/Chromium.
BROWSER_PATHS: Final[list[str]] = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome",
    "/Applications/Comet.app/Contents/MacOS/Comet",  # Fallback only
]

# Browser timeouts
PAGE_LOAD_TIMEOUT: Final[int] = 30  # Seconds
SCRIPT_TIMEOUT: Final[int] = 10  # Seconds
PAGE_SETTLE_DELAY: Final[float] = 1.5  # Seconds
ANIMATION_INIT_DELAY: Final[float] = 0.5  # Seconds
ANIMATION_PAUSE_DELAY: Final[float] = 0.1  # Seconds
VIEWPORT_CORRECTION_DELAY: Final[float] = 0.5  # Seconds

# ==============================================================================
# PROCESSING LIMITS
# ==============================================================================

# Max: 4K @ 60fps for 60 seconds
MAX_PIXEL_FRAMES: Final[int] = 3840 * 2160 * 60 * 60

# ==============================================================================
# UPSCALING CONFIGURATION
# ==============================================================================

UPSCALE_THRESHOLD: Final[float] = 1.5  # When to use advanced upscaling
LANCZOS_SCALER: Final[str] = "lanczos"
SPLINE_SCALER: Final[str] = "spline36"

# Sharpening filters (FFmpeg unsharp format)
NORMAL_SHARPEN: Final[str] = "unsharp=5:5:1.0:5:5:0.0"
STRONG_SHARPEN: Final[str] = "unsharp=7:7:1.5:7:7:0.0"

# ==============================================================================
# UI CONFIGURATION
# ==============================================================================

UI_PRIMARY_COLOR: Final[str] = "#ff8c42"
UI_BACKGROUND_COLOR: Final[str] = "#1a1a1a"
UI_SECONDARY_BG_COLOR: Final[str] = "#2d2d2d"
UI_TEXT_COLOR: Final[str] = "#ffffff"

# ==============================================================================
# REGEX PATTERNS FOR HTML ANALYSIS
# ==============================================================================

WIDTH_PATTERNS: Final[list[str]] = [
    r'viewport.*width["\s:=]+(\d+)',
    r'width:\s*(\d+)px',
    r'canvas.*width["\s:=]+(\d+)',
    r'<meta.*content=.*width=(\d+)',
]

HEIGHT_PATTERNS: Final[list[str]] = [
    r'viewport.*height["\s:=]+(\d+)',
    r'height:\s*(\d+)px',
    r'canvas.*height["\s:=]+(\d+)',
    r'<meta.*content=.*height=(\d+)',
]

DURATION_PATTERNS: Final[list[str]] = [
    r'duration["\s:=]+(\d+)',
    r'animation.*?(\d+)s',
    r'setTimeout.*?(\d+)\s*\*\s*1000',
]


# ==============================================================================
# DATA CLASSES
# ==============================================================================

@dataclass
class VideoConfig:
    """
    Configuration for video output.
    
    Attributes:
        width: Video width in pixels
        height: Video height in pixels
        fps: Frames per second
        duration: Video duration in seconds
        codec: Video codec (default: libx264)
        bitrate: Target bitrate (default: 10M)
        animation_speed: Playback speed multiplier (1.0 = normal)
        preset: FFmpeg encoding preset (default: slow)
        crf: Constant Rate Factor for quality (default: 18)
        target_format: "auto", "square", or "vertical"
    """
    width: int
    height: int
    fps: int
    duration: int
    codec: str = DEFAULT_CODEC
    bitrate: str = DEFAULT_BITRATE
    animation_speed: float = DEFAULT_ANIMATION_SPEED
    preset: str = DEFAULT_PRESET
    crf: int = DEFAULT_CRF
    target_format: str = "auto"  # "auto", "square", or "vertical"


@dataclass
class HTMLAnalysisResult:
    """
    Result of HTML5 content analysis.
    
    Attributes:
        width: Detected width in pixels
        height: Detected height in pixels
        duration: Detected animation duration in seconds
        fps: Recommended FPS based on animation complexity
        has_animations: Whether animations were detected
    """
    width: int
    height: int
    duration: int
    fps: int
    has_animations: bool


@dataclass
class DimensionFit:
    """
    Information about how source content fits into target dimensions.
    
    Attributes:
        fit_width: Width after proportional scaling
        fit_height: Height after proportional scaling
        pad_top: Top padding in pixels
        pad_bottom: Bottom padding in pixels
        pad_left: Left padding in pixels
        pad_right: Right padding in pixels
        needs_padding: Whether padding is required
    """
    fit_width: int
    fit_height: int
    pad_top: int
    pad_bottom: int
    pad_left: int
    pad_right: int
    needs_padding: bool

