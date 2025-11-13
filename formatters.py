"""
Format conversion and aspect ratio handling for social media.
"""
from config import (
    DimensionFit,
    SQUARE_FORMAT,
    VERTICAL_FORMAT,
    SQUARE_ASPECT_RATIO,
    VERTICAL_ASPECT_RATIO,
    UPSCALE_THRESHOLD,
    LANCZOS_SCALER,
    SPLINE_SCALER,
    NORMAL_SHARPEN,
    STRONG_SHARPEN,
)


class SocialMediaFormatter:
    """
    Handles social media format detection and CSS generation.
    
    This class determines the best social media format (square/vertical)
    for given content dimensions and generates CSS for proportional scaling.
    """
    
    @staticmethod
    def detect_best_format(source_width: int, source_height: int) -> tuple[int, int, str]:
        """
        Detect optimal social media format based on source aspect ratio.
        
        Compares source aspect ratio against standard formats:
        - Square (1:1): Instagram posts, general social media
        - Vertical (9:16): Instagram/Facebook Stories, TikTok
        
        Args:
            source_width: Source content width
            source_height: Source content height
            
        Returns:
            Tuple of (width, height, format_name) for the closest match
            
        Example:
            >>> detect_best_format(1920, 1080)  # 16:9 landscape
            (1080, 1080, "1080x1080 (Square/Instagram)")
            >>> detect_best_format(720, 1280)  # 9:16 portrait
            (1080, 1920, "1080x1920 (Vertical/Stories)")
        """
        source_aspect = source_width / source_height
        
        # Calculate distance from each standard format
        square_diff = abs(source_aspect - SQUARE_ASPECT_RATIO)
        vertical_diff = abs(source_aspect - VERTICAL_ASPECT_RATIO)
        
        # Return the closest match
        if square_diff < vertical_diff:
            return SQUARE_FORMAT
        else:
            return VERTICAL_FORMAT
    
    @staticmethod
    def generate_scaling_css(
        target_width: int,
        target_height: int,
        source_width: int,
        source_height: int,
        bg_color: str = "#000000"
    ) -> str:
        """
        Generate CSS for proportional scaling and centering of content.
        
        This creates CSS that:
        1. Sets viewport to target dimensions
        2. Calculates proportional scale factor
        3. Centers scaled content with padding
        4. Applies background color to padding areas
        
        Args:
            target_width: Target frame width
            target_height: Target frame height
            source_width: Original content width
            source_height: Original content height
            bg_color: Background color for padding (hex format)
            
        Returns:
            CSS string to inject into HTML
        """
        # Calculate proportional scale to fit without distortion
        scale_x = target_width / source_width
        scale_y = target_height / source_height
        scale = min(scale_x, scale_y)  # Use minimum to fit within bounds
        
        # Calculate final scaled dimensions
        scaled_width = source_width * scale
        scaled_height = source_height * scale
        
        # Calculate centering offsets
        offset_x = (target_width - scaled_width) / 2
        offset_y = (target_height - scaled_height) / 2
        
        return f"""
        <style id="format-override">
        html, body {{
            margin: 0 !important;
            padding: 0 !important;
            width: {target_width}px !important;
            height: {target_height}px !important;
            overflow: hidden !important;
            background: {bg_color} !important;
        }}
        #scale-wrapper {{
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


class AspectRatioCalculator:
    """
    Calculates aspect ratio fitting and generates FFmpeg scaling filters.
    
    This class handles the math for fitting source content into target
    dimensions without distortion, calculating required padding, and
    generating appropriate FFmpeg filter chains.
    """
    
    @staticmethod
    def calculate_fit(
        source_width: int,
        source_height: int,
        target_width: int,
        target_height: int
    ) -> DimensionFit:
        """
        Calculate how source content fits into target dimensions.
        
        Preserves aspect ratio by scaling proportionally and adding
        letterboxing (top/bottom bars) or pillarboxing (left/right bars).
        
        Args:
            source_width: Original content width
            source_height: Original content height
            target_width: Desired output width
            target_height: Desired output height
            
        Returns:
            DimensionFit object with scaled dimensions and padding info
            
        Example:
            >>> calculate_fit(1920, 1080, 1080, 1080)  # 16:9 to square
            DimensionFit(fit_width=1080, fit_height=608, pad_top=236, ...)
        """
        source_aspect = source_width / source_height
        target_aspect = target_width / target_height
        
        # Check if aspects are nearly identical (within 1%)
        if abs(source_aspect - target_aspect) < 0.01:
            return DimensionFit(
                fit_width=target_width,
                fit_height=target_height,
                pad_top=0,
                pad_bottom=0,
                pad_left=0,
                pad_right=0,
                needs_padding=False
            )
        
        if source_aspect > target_aspect:
            # Source is wider → fit to width, add top/bottom bars
            fit_width = target_width
            fit_height = int(target_width / source_aspect)
            
            # Ensure even dimensions for H.264 compatibility
            if fit_height % 2 != 0:
                fit_height -= 1
            
            pad_top = (target_height - fit_height) // 2
            pad_bottom = target_height - fit_height - pad_top
            
            return DimensionFit(
                fit_width=fit_width,
                fit_height=fit_height,
                pad_top=pad_top,
                pad_bottom=pad_bottom,
                pad_left=0,
                pad_right=0,
                needs_padding=True
            )
        else:
            # Source is taller → fit to height, add left/right bars
            fit_height = target_height
            fit_width = int(target_height * source_aspect)
            
            # Ensure even dimensions for H.264 compatibility
            if fit_width % 2 != 0:
                fit_width -= 1
            
            pad_left = (target_width - fit_width) // 2
            pad_right = target_width - fit_width - pad_left
            
            return DimensionFit(
                fit_width=fit_width,
                fit_height=fit_height,
                pad_top=0,
                pad_bottom=0,
                pad_left=pad_left,
                pad_right=pad_right,
                needs_padding=True
            )
    
    @staticmethod
    def generate_ffmpeg_filter(
        source_width: int,
        source_height: int,
        target_width: int,
        target_height: int,
        enable_advanced_upscaling: bool = False
    ) -> str:
        """
        Generate FFmpeg filter chain for scaling with quality preservation.
        
        Chooses optimal scaler based on scale factor:
        - Large upscaling (>1.5x): spline36 + strong sharpening
        - Normal scaling: lanczos + normal sharpening
        
        Also handles padding if aspect ratios don't match.
        
        Args:
            source_width: Original content width
            source_height: Original content height
            target_width: Desired output width
            target_height: Desired output height
            enable_advanced_upscaling: Use advanced upscaling for large scale factors
            
        Returns:
            FFmpeg filter string (e.g., "scale=1920:1080:flags=lanczos,unsharp=...")
        """
        fit_info = AspectRatioCalculator.calculate_fit(
            source_width, source_height, target_width, target_height
        )
        
        # Determine scale factor
        scale_factor_w = target_width / source_width
        scale_factor_h = target_height / source_height
        scale_factor = max(scale_factor_w, scale_factor_h)
        
        # Choose scaler and sharpening based on scale factor
        if enable_advanced_upscaling and scale_factor > UPSCALE_THRESHOLD:
            scaler = SPLINE_SCALER
            sharpen_filter = STRONG_SHARPEN
        else:
            scaler = LANCZOS_SCALER
            sharpen_filter = NORMAL_SHARPEN
        
        filter_parts = []
        
        if fit_info.needs_padding:
            # Scale to fit, sharpen, then pad to target
            filter_parts.append(
                f"scale={fit_info.fit_width}:{fit_info.fit_height}:flags={scaler}"
            )
            filter_parts.append(sharpen_filter)
            filter_parts.append(
                f"pad={target_width}:{target_height}:"
                f"{fit_info.pad_left}:{fit_info.pad_top}:black"
            )
        else:
            # Just scale and sharpen (no padding needed)
            filter_parts.append(
                f"scale={target_width}:{target_height}:flags={scaler}"
            )
            filter_parts.append(sharpen_filter)
        
        return ",".join(filter_parts)

