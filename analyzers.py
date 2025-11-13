"""
HTML5 content analysis for automatic parameter detection.
"""
import re
from typing import Optional

from config import (
    HTMLAnalysisResult,
    MIN_DIMENSION,
    MAX_WIDTH,
    MAX_HEIGHT,
    MAX_AUTO_DETECTED_DURATION,
    DEFAULT_DURATION,
    HIGH_ANIMATION_THRESHOLD,
    MEDIUM_ANIMATION_THRESHOLD,
    HIGH_FPS,
    MEDIUM_FPS,
    LOW_FPS,
    ANIMATION_KEYWORDS,
    WIDTH_PATTERNS,
    HEIGHT_PATTERNS,
    DURATION_PATTERNS,
)


class HTML5Analyzer:
    """
    Analyzes HTML5 content to auto-detect optimal video settings.
    
    This class examines HTML files to extract:
    - Viewport dimensions (width/height)
    - Animation duration
    - Recommended FPS based on animation complexity
    """
    
    def __init__(self, default_width: int = 1920, default_height: int = 1080):
        """
        Initialize analyzer with default dimensions.
        
        Args:
            default_width: Fallback width if detection fails
            default_height: Fallback height if detection fails
        """
        self.default_width = default_width
        self.default_height = default_height
    
    def analyze_html(self, html_path: str) -> HTMLAnalysisResult:
        """
        Analyze HTML file to detect resolution and animation parameters.
        
        This method:
        1. Reads the HTML content
        2. Searches for viewport/canvas dimensions using regex
        3. Detects animation duration from CSS/JS
        4. Calculates recommended FPS based on animation complexity
        
        Args:
            html_path: Path to HTML file to analyze
            
        Returns:
            HTMLAnalysisResult with detected parameters
        """
        try:
            with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            # If file can't be read, return defaults
            return HTMLAnalysisResult(
                width=self.default_width,
                height=self.default_height,
                duration=DEFAULT_DURATION,
                fps=HIGH_FPS,
                has_animations=False
            )
        
        # Detect dimensions
        width = self._detect_dimension(content, WIDTH_PATTERNS, self.default_width)
        height = self._detect_dimension(content, HEIGHT_PATTERNS, self.default_height)
        
        # Detect animation duration
        duration = self._detect_duration(content)
        
        # Detect recommended FPS based on animation complexity
        fps, has_animations = self._detect_fps(content)
        
        return HTMLAnalysisResult(
            width=width,
            height=height,
            duration=duration,
            fps=fps,
            has_animations=has_animations
        )
    
    def _detect_dimension(
        self,
        content: str,
        patterns: list[str],
        default: int
    ) -> int:
        """
        Detect a single dimension (width or height) from HTML content.
        
        Args:
            content: HTML content to search
            patterns: List of regex patterns to try
            default: Default value if detection fails
            
        Returns:
            Detected dimension in pixels, or default if not found
        """
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                detected = int(match.group(1))
                # Validate dimension is reasonable
                if MIN_DIMENSION <= detected <= MAX_WIDTH:
                    return detected
        
        return default
    
    def _detect_duration(self, content: str) -> int:
        """
        Detect animation duration from HTML content.
        
        Searches for:
        - CSS animation duration properties
        - setTimeout() calls with duration
        - Explicit duration variables
        
        Args:
            content: HTML content to search
            
        Returns:
            Detected duration in seconds (capped at MAX_AUTO_DETECTED_DURATION)
        """
        detected_durations = []
        
        for pattern in DURATION_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                # Convert to integers and filter out unreasonably large values
                # (these are likely false positives like timestamps)
                durations = [
                    int(m) for m in matches
                    if int(m) < 1000  # Ignore values >1000 seconds
                ]
                detected_durations.extend(durations)
        
        if detected_durations:
            # Use the maximum duration found (animations may layer/sequence)
            max_duration = max(detected_durations)
            # Cap at maximum to prevent false positives
            return min(max_duration, MAX_AUTO_DETECTED_DURATION)
        
        return DEFAULT_DURATION
    
    def _detect_fps(self, content: str) -> tuple[int, bool]:
        """
        Determine recommended FPS based on animation complexity.
        
        Counts animation-related keywords to estimate complexity:
        - High complexity (>10 keywords): 60 FPS for smooth animations
        - Medium complexity (4-10): 30 FPS for standard animations  
        - Low complexity (<4): 24 FPS for basic content
        
        Args:
            content: HTML content to search
            
        Returns:
            Tuple of (recommended_fps, has_animations)
        """
        content_lower = content.lower()
        animation_count = sum(
            content_lower.count(keyword) for keyword in ANIMATION_KEYWORDS
        )
        
        has_animations = animation_count > 0
        
        if animation_count > HIGH_ANIMATION_THRESHOLD:
            return HIGH_FPS, has_animations
        elif animation_count > MEDIUM_ANIMATION_THRESHOLD:
            return MEDIUM_FPS, has_animations
        else:
            return LOW_FPS, has_animations

