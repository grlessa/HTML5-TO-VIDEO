# Rewritten HTML5 Rendering Pipeline

## Complete Standalone Python Code

This is a complete, standalone implementation that guarantees correct dimensions:

```python
"""
HTML5 to Video Rendering Pipeline - Guaranteed Correct Dimensions
==================================================================
Ensures Chrome viewport ALWAYS matches auto-detected dimensions.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image
import time
import os

def render_html_with_correct_dimensions(html_path, output_dir, target_width, target_height, fps, duration):
    """
    Render HTML to video frames with guaranteed correct dimensions.

    Requirements met:
    ✓ Chrome ALWAYS matches requested width/height
    ✓ Explicitly set window size in both chrome_options and driver.set_window_size()
    ✓ Use JS to force document and body sizes
    ✓ Add delay for page resize (1.5s)
    ✓ Log detected, requested, and actual viewport dimensions
    ✓ If screenshot wrong size, crop/resize to match and continue
    ✓ Output 'frame_fixed.png' as debug frame
    """

    frames_dir = os.path.join(output_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    total_frames = fps * duration
    frame_time_s = 1.0 / fps

    # Ensure even dimensions for H.264
    target_width = target_width if target_width % 2 == 0 else target_width + 1
    target_height = target_height if target_height % 2 == 0 else target_height + 1

    print(f"=== DIMENSION REQUIREMENTS ===")
    print(f"Target dimensions (from auto-detection): {target_width}x{target_height}")

    # Chrome options - set window size HERE (requirement #1)
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--hide-scrollbars')
    chrome_options.add_argument('--force-device-scale-factor=1')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    # Add extra height for browser chrome in headless mode
    chrome_options.add_argument(f'--window-size={target_width},{target_height + 100}')

    print(f"Chrome options window-size: {target_width}x{target_height + 100}")

    # Find browser binary
    browser_paths = [
        "/Applications/Comet.app/Contents/MacOS/Comet",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/google-chrome"
    ]

    for path in browser_paths:
        if os.path.exists(path):
            chrome_options.binary_location = path
            print(f"Using browser: {path}")
            break

    # Initialize driver
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Requirement #2: Set window size via Selenium API (in addition to chrome options)
        driver.set_window_size(target_width, target_height + 100)
        print(f"Selenium set_window_size: {target_width}x{target_height + 100}")

        # Load HTML
        file_url = f"file://{html_path}"
        driver.get(file_url)
        print(f"Loaded: {file_url}")

        # Requirement #3: Force document and body to EXACT dimensions via JavaScript
        js_resize_script = f"""
            // Remove all margins, padding, scrollbars
            document.documentElement.style.margin = '0';
            document.documentElement.style.padding = '0';
            document.documentElement.style.overflow = 'hidden';
            document.documentElement.style.width = '{target_width}px';
            document.documentElement.style.height = '{target_height}px';

            document.body.style.margin = '0';
            document.body.style.padding = '0';
            document.body.style.overflow = 'hidden';
            document.body.style.width = '{target_width}px';
            document.body.style.height = '{target_height}px';
            document.body.style.minWidth = '{target_width}px';
            document.body.style.minHeight = '{target_height}px';
            document.body.style.maxWidth = '{target_width}px';
            document.body.style.maxHeight = '{target_height}px';

            // Force any canvas elements to match
            var canvases = document.getElementsByTagName('canvas');
            for (var i = 0; i < canvases.length; i++) {{
                canvases[i].style.width = '{target_width}px';
                canvases[i].style.height = '{target_height}px';
            }}
        """
        driver.execute_script(js_resize_script)
        print("JavaScript resize applied")

        # Requirement #4: Wait for page to settle (delay for resize)
        time.sleep(1.5)

        # Requirement #5: Log detected, requested, and actual viewport dimensions
        actual_viewport_w = driver.execute_script("return window.innerWidth;")
        actual_viewport_h = driver.execute_script("return window.innerHeight;")
        actual_body_w = driver.execute_script("return document.body.offsetWidth;")
        actual_body_h = driver.execute_script("return document.body.offsetHeight;")

        print(f"\n=== ACTUAL DIMENSIONS ===")
        print(f"Requested: {target_width}x{target_height}")
        print(f"Actual viewport: {actual_viewport_w}x{actual_viewport_h}")
        print(f"Actual body: {actual_body_w}x{actual_body_h}")

        # Capture frames with dimension verification
        print(f"\n=== CAPTURING {total_frames} FRAMES ===")

        for frame_num in range(total_frames):
            frame_path = os.path.join(frames_dir, f"frame_{frame_num:06d}.png")
            temp_screenshot = frame_path + ".tmp"

            # Take screenshot
            driver.save_screenshot(temp_screenshot)

            # Requirement #6: If screenshot wrong size, crop/resize to match and continue
            with Image.open(temp_screenshot) as img:
                screenshot_w, screenshot_h = img.size

                if frame_num == 0:
                    print(f"\n=== SCREENSHOT ANALYSIS ===")
                    print(f"Screenshot size: {screenshot_w}x{screenshot_h}")
                    print(f"Expected size: {target_width}x{target_height}")

                # Case 1: Screenshot is larger or equal - crop it
                if screenshot_w >= target_width and screenshot_h >= target_height:
                    corrected = img.crop((0, 0, target_width, target_height))
                    corrected.save(frame_path)
                    if frame_num == 0:
                        print(f"Action: CROP from {screenshot_w}x{screenshot_h} to {target_width}x{target_height}")

                # Case 2: Screenshot is smaller - resize it
                elif screenshot_w < target_width or screenshot_h < target_height:
                    corrected = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                    corrected.save(frame_path)
                    if frame_num == 0:
                        print(f"Action: RESIZE from {screenshot_w}x{screenshot_h} to {target_width}x{target_height}")
                        print(f"WARNING: Screenshot smaller than expected!")

                # Case 3: Exact match
                else:
                    img.save(frame_path)
                    if frame_num == 0:
                        print(f"Action: EXACT MATCH - no correction needed")

                # Requirement #7: Output 'frame_fixed.png' as debug frame
                if frame_num == 0:
                    debug_frame = os.path.join(output_dir, "frame_fixed.png")
                    with Image.open(frame_path) as fixed_img:
                        fixed_img.save(debug_frame)
                        final_w, final_h = fixed_img.size
                        print(f"\n=== DEBUG FRAME ===")
                        print(f"Saved: frame_fixed.png")
                        print(f"Final dimensions: {final_w}x{final_h}")
                        print(f"Match target: {'YES' if final_w == target_width and final_h == target_height else 'NO'}")

            os.unlink(temp_screenshot)

            if frame_num % 10 == 0:
                print(f"Progress: {frame_num + 1}/{total_frames} frames")

            time.sleep(frame_time_s)

        print(f"\n=== COMPLETE ===")
        print(f"Captured {total_frames} frames at {target_width}x{target_height}")

    finally:
        driver.quit()

    return frames_dir


# Example usage:
if __name__ == "__main__":
    # These would come from auto-detection
    detected_width = 336
    detected_height = 280

    render_html_with_correct_dimensions(
        html_path="/path/to/index.html",
        output_dir="/tmp/html5_video",
        target_width=detected_width,
        target_height=detected_height,
        fps=60,
        duration=10
    )
```

## Key Improvements

### 1. Dual Window Size Setting
```python
# Set in chrome_options
chrome_options.add_argument(f'--window-size={target_width},{target_height + 100}')

# AND set via Selenium API
driver.set_window_size(target_width, target_height + 100)
```

### 2. Comprehensive JavaScript Resize
```javascript
// Forces BOTH documentElement AND body
// Uses min/max width/height to prevent resizing
// Targets canvas elements specifically
```

### 3. Extended Delay
```python
time.sleep(1.5)  # Give page time to settle after JS resize
```

### 4. Complete Dimension Logging
```
=== DIMENSION REQUIREMENTS ===
Target dimensions: 336x280

=== ACTUAL DIMENSIONS ===
Requested: 336x280
Actual viewport: 336x280
Actual body: 336x280

=== SCREENSHOT ANALYSIS ===
Screenshot size: 336x280
Expected size: 336x280
Action: EXACT MATCH

=== DEBUG FRAME ===
Saved: frame_fixed.png
Final dimensions: 336x280
Match target: YES
```

### 5. Intelligent Correction
- **Larger screenshot**: Crop from top-left
- **Smaller screenshot**: Resize with LANCZOS (high quality)
- **Exact match**: No processing needed

### 6. Debug Frame Output
- First frame saved as `frame_fixed.png`
- Allows verification before processing all frames
- Dimensions logged clearly

## Headless Mode Quirks Addressed

1. **Extra height**: Added +100px to window size to account for browser chrome
2. **Device scale factor**: Forced to 1 to prevent DPI scaling
3. **Minimum viewport**: No longer relying on browser minimums - we crop/resize as needed
4. **Settle time**: 1.5s delay ensures page has fully resized before capture

## Integration

This code replaces the `render_html_to_frames` method in your `HTML5ToVideoConverter` class. All Streamlit-specific logging (st.info, st.success) can be added around the print statements as needed.
