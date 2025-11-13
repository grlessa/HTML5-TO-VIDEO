#!/usr/bin/env python3
"""
HTML5 to Video Converter - Streamlit Web Application

Converts HTML5 animations and banner ads to video files with automatic
parameter detection and social media format conversion.
"""
import os
import tempfile
import zipfile
import shutil
from pathlib import Path

import streamlit as st

# Import our refactored modules
from config import (
    VideoConfig,
    MAX_ZIP_FILE_SIZE,
    MAX_PIXEL_FRAMES,
    UI_PRIMARY_COLOR,
    UI_BACKGROUND_COLOR,
    UI_SECONDARY_BG_COLOR,
    UI_TEXT_COLOR,
    DEFAULT_CODEC,
    DEFAULT_PRESET,
    DEFAULT_CRF,
    DEFAULT_BITRATE,
    DEFAULT_ANIMATION_SPEED,
)
from analyzers import HTML5Analyzer
from formatters import SocialMediaFormatter
from converter import HTML5ToVideoConverter


def apply_custom_styling():
    """Apply custom CSS styling to Streamlit app."""
    st.markdown("""
        <style>
        :root {
            --background: oklch(1 0 0);
            --foreground: oklch(0.1450 0 0);
            --card: oklch(1 0 0);
            --card-foreground: oklch(0.1450 0 0);
            --popover: oklch(1 0 0);
            --popover-foreground: oklch(0.1450 0 0);
            --primary: oklch(0.2050 0 0);
            --primary-foreground: oklch(0.9850 0 0);
            --secondary: oklch(0.9700 0 0);
            --secondary-foreground: oklch(0.2050 0 0);
            --muted: oklch(0.9700 0 0);
            --muted-foreground: oklch(0.5560 0 0);
            --accent: oklch(0.9700 0 0);
            --accent-foreground: oklch(0.2050 0 0);
            --destructive: oklch(0.5770 0.2450 27.3250);
            --destructive-foreground: oklch(1 0 0);
            --border: oklch(0.9220 0 0);
            --input: oklch(0.9220 0 0);
            --ring: oklch(0.7080 0 0);
            --chart-1: oklch(0.8100 0.1000 252);
            --chart-2: oklch(0.6200 0.1900 260);
            --chart-3: oklch(0.5500 0.2200 263);
            --chart-4: oklch(0.4900 0.2200 264);
            --chart-5: oklch(0.4200 0.1800 266);
            --sidebar: oklch(0.9850 0 0);
            --sidebar-foreground: oklch(0.1450 0 0);
            --sidebar-primary: oklch(0.2050 0 0);
            --sidebar-primary-foreground: oklch(0.9850 0 0);
            --sidebar-accent: oklch(0.9700 0 0);
            --sidebar-accent-foreground: oklch(0.2050 0 0);
            --sidebar-border: oklch(0.9220 0 0);
            --sidebar-ring: oklch(0.7080 0 0);
            --font-sans: Inter, ui-sans-serif, sans-serif, system-ui;
            --font-serif: "IBM Plex Serif", ui-serif, serif;
            --font-mono: "Intel One Mono", ui-monospace, monospace;
            --radius: 0.625rem;
            --shadow-2xs: 0 1px 3px 0px hsl(0 0% 0% / 0.05);
            --shadow-xs: 0 1px 3px 0px hsl(0 0% 0% / 0.05);
            --shadow-sm: 0 1px 3px 0px hsl(0 0% 0% / 0.10), 0 1px 2px -1px hsl(0 0% 0% / 0.10);
            --shadow: 0 1px 3px 0px hsl(0 0% 0% / 0.10), 0 1px 2px -1px hsl(0 0% 0% / 0.10);
            --shadow-md: 0 1px 3px 0px hsl(0 0% 0% / 0.10), 0 2px 4px -1px hsl(0 0% 0% / 0.10);
            --shadow-lg: 0 1px 3px 0px hsl(0 0% 0% / 0.10), 0 4px 6px -1px hsl(0 0% 0% / 0.10);
            --shadow-xl: 0 1px 3px 0px hsl(0 0% 0% / 0.10), 0 8px 10px -1px hsl(0 0% 0% / 0.10);
            --shadow-2xl: 0 1px 3px 0px hsl(0 0% 0% / 0.25);
        }

        .dark {
            --background: oklch(0.1450 0 0);
            --foreground: oklch(0.9850 0 0);
            --card: oklch(0.2050 0 0);
            --card-foreground: oklch(0.9850 0 0);
            --popover: oklch(0.2690 0 0);
            --popover-foreground: oklch(0.9850 0 0);
            --primary: oklch(0.9220 0 0);
            --primary-foreground: oklch(0.2050 0 0);
            --secondary: oklch(0.2690 0 0);
            --secondary-foreground: oklch(0.9850 0 0);
            --muted: oklch(0.2690 0 0);
            --muted-foreground: oklch(0.7080 0 0);
            --accent: oklch(0.3710 0 0);
            --accent-foreground: oklch(0.9850 0 0);
            --destructive: oklch(0.7040 0.1910 22.2160);
            --destructive-foreground: oklch(0.9850 0 0);
            --border: oklch(0.2750 0 0);
            --input: oklch(0.3250 0 0);
            --ring: oklch(0.5560 0 0);
            --chart-1: oklch(0.7090 0.0100 56.2590);
            --chart-2: oklch(0.5530 0.0130 58.0710);
            --chart-3: oklch(0.4440 0.0110 73.6390);
            --chart-4: oklch(0.3740 0.0100 67.5580);
            --chart-5: oklch(0.2680 0.0070 34.2980);
            --sidebar: oklch(0.2050 0 0);
            --sidebar-foreground: oklch(0.9850 0 0);
            --sidebar-primary: oklch(0.3740 0.0100 67.5580);
            --sidebar-primary-foreground: oklch(0.9850 0 0);
            --sidebar-accent: oklch(0.2690 0 0);
            --sidebar-accent-foreground: oklch(0.9850 0 0);
            --sidebar-border: oklch(0.2750 0 0);
            --sidebar-ring: oklch(0.4390 0 0);
        }

        .stApp {
            background: var(--background);
            color: var(--foreground);
            font-family: var(--font-sans);
        }

        h1, h2, h3, h4 {
            color: var(--foreground) !important;
            font-family: var(--font-serif);
        }

        .main-title {
            font-size: 48px;
            font-weight: 800;
            text-align: center;
            margin-bottom: 10px;
            color: var(--foreground);
        }

        .stFileUploader {
            background: var(--card);
            border: 2px dashed var(--border);
            border-radius: var(--radius);
            padding: 20px;
            box-shadow: var(--shadow);
        }

        .stFileUploader label,
        .stFileUploader input,
        .stFileUploader div {
            color: var(--foreground);
        }

        .stButton>button {
            background: var(--primary);
            color: var(--primary-foreground);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 12px 30px;
            font-weight: 600;
            font-size: 16px;
            width: 100%;
            box-shadow: var(--shadow-sm);
        }

        .stButton>button:hover {
            background: var(--accent);
            color: var(--accent-foreground);
            box-shadow: var(--shadow-lg);
        }

        .stAlert {
            background: var(--muted);
            color: var(--foreground);
            border-left: 4px solid var(--primary);
            border-radius: var(--radius);
        }

        .streamlit-expanderHeader {
            background: var(--secondary);
            color: var(--secondary-foreground) !important;
            border-radius: var(--radius);
            font-size: 14px;
        }

        .stProgress > div > div {
            background: var(--primary);
        }

        .stMetricLabel, .stMetricValue {
            color: var(--foreground) !important;
        }

        .stVideo {
            background: var(--card);
            border-radius: var(--radius);
            padding: 12px;
            box-shadow: var(--shadow);
        }

        .stVideo video {
            max-height: 500px !important;
            width: 100% !important;
            object-fit: contain !important;
        }

        .stTabs [data-baseweb="tab"] {
            background: var(--secondary);
            color: var(--secondary-foreground);
            border-radius: calc(var(--radius) - 4px) calc(var(--radius) - 4px) 0 0;
        }

        .stTabs [aria-selected="true"] {
            background: var(--primary);
            color: var(--primary-foreground);
        }

        .stTextInput>div>div>input,
        .stNumberInput input,
        .stSelectbox>div>div>div {
            background: var(--input);
            color: var(--foreground);
            border-radius: var(--radius);
            border: 1px solid var(--border);
        }

        .stTextInput>div>div>input:focus,
        .stNumberInput input:focus,
        .stSelectbox>div>div>div:focus-within {
            border-color: var(--ring);
            box-shadow: 0 0 0 1px var(--ring);
        }

        .stDownloadButton>button {
            background: var(--secondary);
            color: var(--secondary-foreground);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 12px 20px;
            font-weight: 600;
            width: 100%;
            box-shadow: var(--shadow-sm);
        }

        .stDownloadButton>button:hover {
            background: var(--accent);
            color: var(--accent-foreground);
            box-shadow: var(--shadow-lg);
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        .stMarkdown, .stText, .stCaption {
            color: var(--foreground);
        }
        </style>
    """, unsafe_allow_html=True)


def analyze_uploaded_html_from_path(zip_path: str) -> tuple:
    """
    Analyze HTML5 content from a ZIP file to detect parameters.
    
    Args:
        zip_path: Path to ZIP file
        
    Returns:
        Tuple of (detected_width, detected_height, detected_fps, detected_duration)
    """
    # Extract ZIP to analyze HTML
    temp_extract = tempfile.mkdtemp()
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_extract)
        
        # Find and analyze HTML file
        html_files = list(Path(temp_extract).rglob("*.html"))
        if html_files:
            # Find index.html or use first file
            main_html = None
            for html_file in html_files:
                if html_file.name.lower() in ['index.html', 'index.htm']:
                    main_html = html_file
                    break
            if not main_html:
                main_html = html_files[0]
            
            # Analyze HTML
            analyzer = HTML5Analyzer()
            analysis_result = analyzer.analyze_html(str(main_html))
            
            return (
                analysis_result.width,
                analysis_result.height,
                analysis_result.fps,
                analysis_result.duration
            )
    except Exception:
        # Return defaults if analysis fails
        pass
    finally:
        # Cleanup extraction directory
        shutil.rmtree(temp_extract, ignore_errors=True)
    
    # Return defaults if analysis fails
    return 1920, 1080, 60, 10


def validate_uploaded_file(uploaded_file) -> tuple[bool, str]:
    """
    Validate uploaded file.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file extension
    if not uploaded_file.name.lower().endswith('.zip'):
        return False, "Please upload a ZIP file"
    
    # Check file size
    if uploaded_file.size > MAX_ZIP_FILE_SIZE:
        size_mb = uploaded_file.size / (1024 * 1024)
        max_mb = MAX_ZIP_FILE_SIZE / (1024 * 1024)
        return False, f"File too large ({size_mb:.1f} MB). Maximum: {max_mb} MB"
    
    return True, ""


def validate_processing_load(width: int, height: int, fps: int, duration: int) -> tuple[bool, str]:
    """
    Validate that processing load is within limits.
    
    Args:
        width: Video width
        height: Video height
        fps: Frames per second
        duration: Duration in seconds
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    total_pixel_frames = width * height * fps * duration
    
    if total_pixel_frames > MAX_PIXEL_FRAMES:
        return False, (
            f"Configuration too demanding. Total processing load: {total_pixel_frames:,} pixel-frames. "
            f"Maximum: {MAX_PIXEL_FRAMES:,}. Try reducing duration or resolution."
        )
    
    return True, ""


def main():
    """Main Streamlit application."""
    
    # Page configuration
    st.set_page_config(
        page_title="HTML5 to Video Converter",
        page_icon="🎥",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply custom styling
    apply_custom_styling()
    
    # Header
    st.markdown('<h1 class="main-title">HTML5 to Video Converter</h1>', unsafe_allow_html=True)
    
    # Two-column layout
    left_col, right_col = st.columns([2, 1])
    
    # Right column: Preview area (initialized early)
    with right_col:
        st.markdown("### Preview")
        preview_placeholder = st.empty()
        preview_placeholder.info("Upload a file to see the preview here")
        download_placeholder = st.empty()
    
    # Left column: Upload and settings
    with left_col:
        # File upload
        uploaded_file = st.file_uploader(
            "Upload HTML5 ZIP file",
            type=['zip'],
            help="ZIP file containing HTML, CSS, JS, images, and all assets"
        )
        
        if uploaded_file:
            # Validate file
            is_valid, error_message = validate_uploaded_file(uploaded_file)
            if not is_valid:
                st.error(f"❌ {error_message}")
                st.stop()
            
            # Save uploaded file (will be reused for conversion)
            temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
            temp_zip.write(uploaded_file.read())
            temp_zip.close()
            
            # Analyze HTML5 content from the saved file
            with st.spinner("Analyzing HTML5 content..."):
                detected_width, detected_height, detected_fps, detected_duration = \
                    analyze_uploaded_html_from_path(temp_zip.name)
            
            # Use detected values
            width = detected_width
            height = detected_height
            fps = detected_fps
            
            # Settings section
            with st.expander("⚙️ Settings", expanded=True):
                # Show detected values as metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Resolution", f"{width}x{height}")
                with col2:
                    st.metric("FPS", fps)
                with col3:
                    st.metric("Quality", "High")
                
                # Compact controls
                col1, col2 = st.columns(2)
                
                with col1:
                    # Duration control
                    use_custom_duration = st.checkbox(
                        "Custom duration",
                        value=False,
                        key="custom_duration"
                    )
                    if use_custom_duration:
                        duration = st.number_input(
                            "Seconds",
                            min_value=1,
                            max_value=300,
                            value=detected_duration,
                            key="duration_input"
                        )
                    else:
                        duration = detected_duration
                        st.caption(f"{detected_duration}s (auto-detected)")
                
                with col2:
                    # Format control
                    auto_width, auto_height, auto_format_name = \
                        SocialMediaFormatter.detect_best_format(width, height)
                    
                    use_auto_format = st.checkbox(
                        "Auto format",
                        value=True,
                        key="auto_format"
                    )
                    if not use_auto_format:
                        format_option = st.selectbox(
                            "Format",
                            ["1080x1080 (Square)", "1080x1920 (Vertical)"],
                            key="format_select"
                        )
                        target_format = "square" if "Square" in format_option else "vertical"
                    else:
                        st.caption(auto_format_name)
                        target_format = "auto"
            
            # Validate processing load
            is_valid, error_message = validate_processing_load(width, height, fps, duration)
            if not is_valid:
                st.error(f"❌ {error_message}")
                st.stop()
            
            # Convert button
            if st.button("Convert to Video", use_container_width=True):
                # Prepare output filename
                base_name = os.path.splitext(uploaded_file.name)[0]
                output_filename = f"{base_name}.mp4"
                output_path = os.path.join(tempfile.gettempdir(), output_filename)
                
                # Create video configuration
                config = VideoConfig(
                    width=width,
                    height=height,
                    fps=fps,
                    duration=duration,
                    codec=DEFAULT_CODEC,
                    bitrate=DEFAULT_BITRATE,
                    preset=DEFAULT_PRESET,
                    crf=DEFAULT_CRF,
                    animation_speed=DEFAULT_ANIMATION_SPEED,
                    target_format=target_format
                )
                
                # Progress indicators
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Progress callback
                def update_progress(value: float, message: str = None):
                    progress_bar.progress(min(value, 1.0))
                    if message:
                        status_text.text(message)
                
                # Run conversion
                converter = HTML5ToVideoConverter(progress_callback=update_progress)
                success = False
                
                try:
                    success = converter.convert(temp_zip.name, output_path, config)
                except FileNotFoundError as e:
                    error_msg = str(e).lower()
                    if "chrome" in error_msg or "chromium" in error_msg:
                        st.error("❌ Browser not found. Please install Chrome or Chromium.")
                    elif "ffmpeg" in error_msg:
                        st.error("❌ FFmpeg not found. Please install FFmpeg.")
                    else:
                        st.error(f"❌ File not found: {e}")
                    st.info("💡 Check 'Debug Details' below for more information")
                except Exception as e:
                    st.error(f"❌ Conversion failed: {str(e)}")
                    st.info("💡 Check 'Debug Details' below for more information")
                finally:
                    # Cleanup temp ZIP
                    try:
                        if os.path.exists(temp_zip.name):
                            os.unlink(temp_zip.name)
                    except:
                        pass
                
                # Complete progress
                progress_bar.progress(1.0)
                if success:
                    status_text.success("✓ Complete")
                else:
                    status_text.empty()
                    # Cleanup failed output
                    try:
                        if os.path.exists(output_path):
                            os.unlink(output_path)
                    except:
                        pass
                
                # Show debug log
                with st.expander("Debug Details", expanded=False):
                    debug_log = converter.get_debug_log()
                    st.code(debug_log, language="text")
                    st.caption("↑ Complete process log")
                
                # Show result if successful
                if success and os.path.exists(output_path):
                    # Read video into memory
                    with open(output_path, 'rb') as f:
                        video_bytes = f.read()
                    
                    # Update preview in right column
                    preview_placeholder.video(video_bytes)
                    
                    # Add download button
                    download_placeholder.download_button(
                        label="📥 Download Video",
                        data=video_bytes,
                        file_name=output_filename,
                        mime="video/mp4",
                        use_container_width=True
                    )
                    
                    # Cleanup output file (video is in memory)
                    try:
                        os.unlink(output_path)
                    except:
                        pass


if __name__ == "__main__":
    main()
