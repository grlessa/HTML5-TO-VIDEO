#!/usr/bin/env python3
"""
Example usage of the refactored HTML5 to Video Converter API.

This demonstrates how to use the converter programmatically without the Streamlit UI.
"""

from config import VideoConfig
from analyzers import HTML5Analyzer
from formatters import SocialMediaFormatter
from converter import HTML5ToVideoConverter


def basic_conversion():
    """
    Basic example: Convert HTML5 ZIP to video with auto-detected settings.
    """
    print("=== Basic Conversion Example ===\n")
    
    # Step 1: Analyze HTML content (if you want auto-detection)
    # First extract and find HTML file manually, or just use known dimensions
    
    # Step 2: Create configuration
    config = VideoConfig(
        width=1920,
        height=1080,
        fps=60,
        duration=10,
        target_format="auto"  # Auto-detect best social media format
    )
    
    # Step 3: Create converter
    converter = HTML5ToVideoConverter()
    
    # Step 4: Run conversion
    success = converter.convert(
        zip_path="example_test.zip",
        output_path="output.mp4",
        config=config
    )
    
    # Step 5: Check results
    if success:
        print("\n✓ Conversion successful!")
        print(f"Output: output.mp4")
    else:
        print("\n✗ Conversion failed!")
        print("\nDebug log:")
        print(converter.get_debug_log())


def conversion_with_progress():
    """
    Example with progress callback to monitor conversion.
    """
    print("\n=== Conversion with Progress Tracking ===\n")
    
    # Progress callback function
    def show_progress(value: float, message: str = None):
        """Display conversion progress."""
        percent = int(value * 100)
        bar_length = 50
        filled = int(bar_length * value)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        if message:
            print(f"\r[{bar}] {percent}% - {message}", end='', flush=True)
        else:
            print(f"\r[{bar}] {percent}%", end='', flush=True)
    
    # Create configuration for vertical format (Stories/TikTok)
    config = VideoConfig(
        width=720,
        height=1280,
        fps=30,
        duration=15,
        target_format="vertical"  # Force vertical format
    )
    
    # Create converter with progress callback
    converter = HTML5ToVideoConverter(progress_callback=show_progress)
    
    # Run conversion
    success = converter.convert(
        zip_path="example_test.zip",
        output_path="vertical_output.mp4",
        config=config
    )
    
    print()  # New line after progress bar
    
    if success:
        print("\n✓ Vertical video created successfully!")
    else:
        print("\n✗ Conversion failed!")


def analyze_html_example():
    """
    Example: Analyze HTML content before conversion.
    """
    print("\n=== HTML Analysis Example ===\n")
    
    # This would normally work with an extracted HTML file
    # For demonstration, showing the API
    
    analyzer = HTML5Analyzer()
    
    # Analyze would extract dimensions, FPS, duration automatically
    # result = analyzer.analyze_html("path/to/index.html")
    # print(f"Detected dimensions: {result.width}x{result.height}")
    # print(f"Detected FPS: {result.fps}")
    # print(f"Detected duration: {result.duration}s")
    # print(f"Has animations: {result.has_animations}")
    
    print("Analyzer ready - extract HTML from ZIP first")


def format_detection_example():
    """
    Example: Detect optimal social media format.
    """
    print("\n=== Format Detection Example ===\n")
    
    # Test different aspect ratios
    test_cases = [
        (1920, 1080, "16:9 Landscape"),
        (1080, 1920, "9:16 Portrait"),
        (1200, 1200, "1:1 Square"),
        (1280, 720, "16:9 HD"),
        (720, 1280, "9:16 Mobile"),
    ]
    
    for width, height, description in test_cases:
        target_w, target_h, format_name = SocialMediaFormatter.detect_best_format(
            width, height
        )
        print(f"{description:20} ({width}x{height:4}) → {format_name}")


def custom_settings_example():
    """
    Example: Use custom video encoding settings.
    """
    print("\n=== Custom Settings Example ===\n")
    
    # High-quality settings
    high_quality_config = VideoConfig(
        width=3840,        # 4K
        height=2160,
        fps=60,            # Smooth
        duration=10,
        codec="libx265",   # H.265 for better compression
        crf=16,            # Very high quality
        preset="slow",     # Better compression
        target_format="auto"
    )
    
    # Fast/web-friendly settings
    web_config = VideoConfig(
        width=1280,
        height=720,
        fps=30,
        duration=10,
        codec="libx264",
        crf=23,            # Good quality
        preset="fast",     # Faster encoding
        target_format="auto"
    )
    
    # Slow-motion effect (0.5x speed)
    slowmo_config = VideoConfig(
        width=1920,
        height=1080,
        fps=60,
        duration=10,
        animation_speed=0.5,  # Half speed = slow motion
        target_format="auto"
    )
    
    print("High Quality Config:")
    print(f"  Resolution: {high_quality_config.width}x{high_quality_config.height}")
    print(f"  Codec: {high_quality_config.codec}")
    print(f"  CRF: {high_quality_config.crf}")
    
    print("\nWeb-Friendly Config:")
    print(f"  Resolution: {web_config.width}x{web_config.height}")
    print(f"  FPS: {web_config.fps}")
    print(f"  Preset: {web_config.preset}")
    
    print("\nSlow Motion Config:")
    print(f"  Animation Speed: {slowmo_config.animation_speed}x")
    print(f"  FPS: {slowmo_config.fps}")


def main():
    """
    Run all examples.
    """
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  HTML5 to Video Converter - Refactored API Examples       ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    # Run examples
    format_detection_example()
    analyze_html_example()
    custom_settings_example()
    
    # Uncomment to run actual conversions (requires valid ZIP file)
    # basic_conversion()
    # conversion_with_progress()
    
    print("\n" + "="*60)
    print("Examples complete!")
    print("\nTo run actual conversions, uncomment the conversion")
    print("functions and provide a valid HTML5 ZIP file.")
    print("="*60)


if __name__ == "__main__":
    main()

