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
import base64


@dataclass
class VideoConfig:
    """Configuration for video output"""
    width: int
    height: int
    fps: int
    duration: int
    codec: str = "libx264"
    bitrate: str = "10M"
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
                    duration = max(durations)
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


class HTML5ToVideoConverter:
    """Main converter class"""

    def __init__(self):
        self.cancelled = False

    def extract_zip(self, zip_path: str, extract_dir: str) -> str:
        """Extract and find main HTML file"""
        st.info("📦 Extracting HTML5 archive...")

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        html_files = list(Path(extract_dir).rglob("*.html"))

        if not html_files:
            raise FileNotFoundError("No HTML files found in the archive")

        # Look for index.html or use first HTML file
        main_html = None
        for html_file in html_files:
            if html_file.name.lower() in ['index.html', 'index.htm']:
                main_html = html_file
                break

        if not main_html:
            main_html = html_files[0]

        st.success(f"✅ Found: {main_html.name}")
        return str(main_html.absolute())

    def render_html_to_frames(self, html_path: str, output_dir: str, config: VideoConfig) -> Optional[str]:
        """Render HTML to frames using Selenium"""
        st.info("🎬 Initializing browser...")

        frames_dir = os.path.join(output_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)

        total_frames = config.fps * config.duration

        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument(f"--window-size={config.width},{config.height}")
        chrome_options.add_argument("--force-device-scale-factor=1")

        # Detect browser binary location
        browser_paths = [
            "/Applications/Comet.app/Contents/MacOS/Comet",  # Comet (macOS)
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # Chrome (macOS)
            "/usr/bin/chromium",  # Chromium (Linux/Streamlit Cloud)
            "/usr/bin/chromium-browser",  # Chromium (alternative)
            "/usr/bin/google-chrome",  # Chrome (Linux)
        ]

        for path in browser_paths:
            if os.path.exists(path):
                chrome_options.binary_location = path
                st.info(f"Using browser: {os.path.basename(path)}")
                break

        try:
            driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            st.error(f"❌ Browser error: {e}")
            st.info("💡 Make sure packages.txt includes: chromium, chromium-driver")
            with st.expander("Show error details"):
                st.code(str(e), language="text")
            return None

        try:
            driver.set_window_size(config.width, config.height)
            file_url = f"file://{html_path}"
            driver.get(file_url)
            time.sleep(1)

            st.info(f"📸 Capturing {total_frames} frames at {config.fps} FPS...")

            progress_bar = st.progress(0)
            status_text = st.empty()

            frame_time_s = 1.0 / config.fps

            for frame_num in range(total_frames):
                if self.cancelled:
                    driver.quit()
                    return None

                frame_path = os.path.join(frames_dir, f"frame_{frame_num:06d}.png")
                driver.save_screenshot(frame_path)

                progress = (frame_num + 1) / total_frames
                progress_bar.progress(progress)
                status_text.text(f"Frame {frame_num + 1}/{total_frames}")

                time.sleep(frame_time_s)

            driver.quit()
            progress_bar.empty()
            status_text.empty()
            st.success("✅ Frame capture complete!")

        except Exception as e:
            st.error(f"❌ Rendering error: {e}")
            try:
                driver.quit()
            except:
                pass
            return None

        return frames_dir

    def encode_video(self, frames_dir: str, output_path: str, config: VideoConfig) -> bool:
        """Encode frames to video using FFmpeg"""
        st.info("🎥 Encoding video with FFmpeg...")

        input_pattern = os.path.join(frames_dir, "frame_%06d.png")

        # Build FFmpeg command with better compatibility
        # Note: CRF and bitrate should NOT be used together - CRF is constant quality, bitrate is constant bitrate
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-framerate", str(config.fps),
            "-i", input_pattern,
            "-c:v", config.codec,
            "-pix_fmt", "yuv420p",
        ]

        # Add preset and quality settings for x264/x265 codecs
        if config.codec in ["libx264", "libx265"]:
            ffmpeg_cmd.extend(["-preset", config.preset])
            # Use CRF mode (constant quality) - better than bitrate
            ffmpeg_cmd.extend(["-crf", str(config.crf)])
            # Add maxrate for compatibility (soft limit)
            ffmpeg_cmd.extend(["-maxrate", config.bitrate])
            # Calculate buffer size (2x maxrate)
            try:
                bitrate_val = int(config.bitrate.replace('M', '').replace('K', '').replace('k', ''))
                if 'M' in config.bitrate or 'm' in config.bitrate:
                    bufsize = f"{bitrate_val * 2}M"
                else:
                    bufsize = f"{bitrate_val * 2}k"
            except:
                bufsize = "20M"  # Default fallback
            ffmpeg_cmd.extend(["-bufsize", bufsize])
        else:
            # For other codecs, use bitrate mode
            ffmpeg_cmd.extend(["-b:v", config.bitrate])

        # Add final options
        ffmpeg_cmd.extend([
            "-movflags", "+faststart",
            "-strict", "experimental",  # Allow experimental features if needed
        ])

        # Add output path
        ffmpeg_cmd.append(output_path)

        try:
            # Check if frames exist
            frame_files = sorted([f for f in os.listdir(frames_dir) if f.endswith('.png')])
            if not frame_files:
                st.error("❌ No frames found to encode!")
                return False

            st.info(f"🎬 Encoding {len(frame_files)} frames...")

            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # Capture output
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                st.success("✅ Video encoding complete!")
                return True
            else:
                # Show detailed error
                st.error(f"❌ FFmpeg error (exit code {process.returncode})")

                # Show last few lines of error output
                error_lines = stderr.strip().split('\n')
                relevant_errors = [line for line in error_lines if 'error' in line.lower() or 'invalid' in line.lower()]

                if relevant_errors:
                    with st.expander("Show error details"):
                        for line in relevant_errors[-5:]:
                            st.code(line, language="text")
                else:
                    with st.expander("Show FFmpeg output"):
                        st.code(stderr[-2000:], language="text")  # Last 2000 chars

                return False

        except FileNotFoundError:
            st.error("❌ FFmpeg not found. Please install FFmpeg.")
            st.info("On Streamlit Cloud, make sure 'packages.txt' includes 'ffmpeg'")
            return False
        except Exception as e:
            st.error(f"❌ Encoding error: {e}")
            import traceback
            with st.expander("Show error details"):
                st.code(traceback.format_exc(), language="text")
            return False

    def convert(self, zip_path: str, output_path: str, config: VideoConfig) -> bool:
        """Main conversion pipeline"""
        temp_dir = tempfile.mkdtemp(prefix="html5_to_video_")

        try:
            html_path = self.extract_zip(zip_path, temp_dir)
            if not html_path:
                return False

            frames_dir = self.render_html_to_frames(html_path, temp_dir, config)
            if not frames_dir:
                return False

            success = self.encode_video(frames_dir, output_path, config)

            if success:
                file_size = os.path.getsize(output_path) / (1024 * 1024)
                st.success(f"🎉 Success! Video size: {file_size:.2f} MB")

            return success

        except Exception as e:
            st.error(f"❌ Error: {e}")
            return False
        finally:
            try:
                shutil.rmtree(temp_dir)
            except:
                pass


def get_download_link(file_path: str, filename: str) -> str:
    """Generate download link for file"""
    with open(file_path, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}" style="display: inline-block; padding: 12px 24px; background: linear-gradient(135deg, #ff6b35 0%, #ff8c42 100%); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; margin-top: 20px;">📥 Download Video</a>'


def main():
    # Page config
    st.set_page_config(
        page_title="HTML5 to Video Converter",
        page_icon="🎬",
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
        </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<h1 class="main-title">🎬 HTML5 to Video Converter</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Professional conversion with auto-detection and full control</p>', unsafe_allow_html=True)

    # Sidebar for settings
    with st.sidebar:
        st.markdown("### ⚙️ Settings")

        mode = st.radio(
            "Mode",
            ["🤖 Auto (Recommended)", "🎛️ Manual"],
            help="Auto mode detects optimal settings from your HTML5 content"
        )

        st.markdown("---")

        if mode == "🎛️ Manual":
            st.markdown("### 📐 Video Configuration")

            col1, col2 = st.columns(2)
            with col1:
                width = st.number_input("Width (px)", 100, 7680, 1920)
            with col2:
                height = st.number_input("Height (px)", 100, 4320, 1080)

            col1, col2 = st.columns(2)
            with col1:
                fps = st.number_input("FPS", 1, 120, 60)
            with col2:
                duration = st.number_input("Duration (s)", 1, 3600, 10)

            st.markdown("### 🎨 Quality Settings")

            codec = st.selectbox(
                "Codec",
                ["libx264", "libx265", "libvpx-vp9", "prores_ks"],
                help="H.264 recommended for compatibility"
            )

            preset = st.selectbox(
                "Preset",
                ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"],
                index=6,
                help="Slower = better quality"
            )

            crf = st.slider("CRF (Quality)", 0, 51, 18, help="Lower = better quality (18 recommended)")

            bitrate = st.text_input("Bitrate", "10M", help="e.g., 5M, 10M, 20M")

    # Main content
    uploaded_file = st.file_uploader(
        "📦 Upload your HTML5 ZIP file",
        type=['zip'],
        help="ZIP file containing HTML, CSS, JS, images, and all assets"
    )

    if uploaded_file:
        # Save uploaded file
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_zip.write(uploaded_file.read())
        temp_zip.close()

        # Auto-detect if in auto mode
        if mode == "🤖 Auto (Recommended)":
            with st.spinner("🔍 Analyzing HTML5 content..."):
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

                    st.success("✅ Auto-detected settings:")
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Resolution", f"{width}x{height}")
                    col2.metric("FPS", fps)
                    col3.metric("Duration", f"{duration}s")
                    col4.metric("Quality", "High (CRF 18)")

                    # Use optimal settings
                    codec = "libx264"
                    preset = "slow"
                    crf = 18
                    bitrate = "10M"

                else:
                    st.warning("⚠️ No HTML files found, using defaults")
                    width, height, fps, duration = 1920, 1080, 60, 10
                    codec, preset, crf, bitrate = "libx264", "slow", 18, "10M"

                shutil.rmtree(temp_extract)

        # Convert button
        if st.button("🚀 Convert to Video", use_container_width=True):
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
                crf=crf
            )

            converter = HTML5ToVideoConverter()

            with st.spinner("🎬 Converting..."):
                success = converter.convert(temp_zip.name, output_file.name, config)

            if success and os.path.exists(output_file.name):
                st.balloons()

                # Download button
                with open(output_file.name, 'rb') as f:
                    video_bytes = f.read()

                st.download_button(
                    label="📥 Download Video",
                    data=video_bytes,
                    file_name="converted_video.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )

                # Show video preview
                st.video(output_file.name)

                # Cleanup
                try:
                    os.unlink(output_file.name)
                except:
                    pass

        # Cleanup zip
        try:
            os.unlink(temp_zip.name)
        except:
            pass

    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #666; padding: 20px;'>
            <p>Built with ❤️ using Streamlit, Selenium & FFmpeg</p>
            <p style='font-size: 12px;'>Supports H.264, H.265, VP9, and ProRes codecs</p>
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
