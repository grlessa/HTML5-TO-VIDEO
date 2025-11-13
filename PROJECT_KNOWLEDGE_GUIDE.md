# HTML5 to Video Converter - Project Knowledge Guide

## Project Overview

**Purpose**: Convert HTML5 animations and banner ads into MP4 video files with automatic parameter detection and intelligent format conversion.

**Tech Stack**:
- Python 3.9+
- Streamlit (Web UI)
- Selenium + Chrome/Chromium (HTML rendering)
- FFmpeg (Video encoding)
- Pillow (Image processing)

**Version**: v3 (OFICIAL-BACKUP-V3)

---

## Architecture Overview

### Core Components

```
┌─────────────────┐
│  Streamlit UI   │  (User Interface)
└────────┬────────┘
         │
┌────────▼────────────────────────────────────────┐
│          HTML5ToVideoConverter                  │
│  ┌──────────────────────────────────────────┐  │
│  │  1. Extract ZIP    (extract_zip)         │  │
│  │  2. Render Frames  (render_html_to_frames)│ │
│  │  3. Encode Video   (encode_video)        │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
         │
    ┌────┴─────┬──────────┬─────────────┐
    │          │          │             │
┌───▼────┐ ┌──▼─────┐ ┌──▼────────┐ ┌─▼────┐
│HTML5   │ │Format  │ │Smart      │ │FFmpeg│
│Analyzer│ │CSS     │ │Upscaler   │ │      │
└────────┘ └────────┘ └───────────┘ └──────┘
```

---

## Key Classes and Their Roles

### 1. `VideoConfig` (Dataclass)
**Location**: app.py:22-34

Configuration object that holds all video generation parameters:
- `width`, `height`: Video dimensions
- `fps`: Frames per second (24/30/60)
- `duration`: Video length in seconds
- `codec`: Video codec (default: libx264)
- `bitrate`: Video bitrate (default: 10M)
- `animation_speed`: Playback speed multiplier (1.0 = normal)
- `preset`: FFmpeg encoding preset (default: slow)
- `crf`: Constant Rate Factor for quality (default: 18)
- `target_format`: "auto", "square", or "vertical"

### 2. `HTML5Analyzer`
**Location**: app.py:37-119

Analyzes HTML files to auto-detect optimal settings:

**Key Method**: `analyze_html(html_path: str) -> dict`
- Reads HTML content
- Detects width/height using regex patterns for viewport, canvas, meta tags
- Detects animation duration from CSS animations, setTimeout calls
- Determines optimal FPS based on animation complexity
- Returns: `{'width', 'height', 'duration', 'fps', 'detected'}`

**Detection Patterns**:
```python
# Width detection:
- viewport.*width["\s:=]+(\d+)
- width:\s*(\d+)px
- canvas.*width["\s:=]+(\d+)

# Duration detection:
- duration["\s:=]+(\d+)
- animation.*?(\d+)s
- setTimeout.*?(\d+)\s*\*\s*1000
```

**FPS Logic**:
- 60 FPS: >10 animation keywords found
- 30 FPS: 4-10 animation keywords
- 24 FPS: <4 animation keywords

### 3. `FormatCSS`
**Location**: app.py:122-186

Handles social media format conversion (square/vertical).

**Method**: `detect_best_format(source_width, source_height) -> tuple`
- Calculates source aspect ratio
- Compares against standard formats:
  - Square: 1:1 (1080x1080) for Instagram
  - Vertical: 9:16 (1080x1920) for Stories
- Returns closest match: `(width, height, format_name)`

**Method**: `generate_css(width, height, source_width, source_height, bg_color) -> str`
- Creates CSS for proportional scaling and centering
- Calculates scale factor to fit without distortion
- Applies transform and padding

### 4. `SmartUpscaler`
**Location**: app.py:189-290

Intelligent aspect ratio fitting and upscaling.

**Method**: `calculate_fit_dimensions(source_w, source_h, target_w, target_h) -> dict`
- Preserves aspect ratio
- Calculates padding needed (letterbox/pillarbox)
- Returns dimensions and padding info

**Method**: `get_ffmpeg_scale_filter(...) -> str`
- Chooses optimal scaler (lanczos vs spline36)
- Adds unsharp filter for crispness
- Builds FFmpeg filter chain

**Scaling Strategy**:
- If scale factor > 1.5: Use spline36 scaler + stronger sharpening
- Otherwise: Use lanczos scaler + normal sharpening

### 5. `HTML5ToVideoConverter`
**Location**: app.py:293-1403

Main conversion pipeline orchestrator.

**Key Methods**:

#### `extract_zip(zip_path, extract_dir) -> str`
**Location**: app.py:326-390

Security-focused ZIP extraction:
- Validates ZIP is not empty
- Prevents ZIP bombs (max 1000 files, 50MB uncompressed)
- Checks for path traversal attacks
- Finds index.html or first HTML file
- Returns path to main HTML file

#### `render_html_to_frames(html_path, output_dir, config) -> tuple`
**Location**: app.py:392-1043

Most complex method - renders HTML to individual frames:

**Process**:
1. **Setup Phase** (lines 405-446):
   - Detect or use configured target format
   - Calculate proportional scale factor
   - Determine padding for centering

2. **Browser Initialization** (lines 449-498):
   - Configure Chrome in headless mode
   - Set window size to target resolution
   - Find browser binary (Comet/Chrome/Chromium)
   - Create Selenium WebDriver

3. **Page Loading** (lines 501-566):
   - Load HTML file
   - Extract background color for padding
   - Apply proportional scaling CSS

4. **Viewport Setup** (lines 567-650):
   - Force exact viewport dimensions
   - Create wrapper div for scaled content
   - Apply CSS transform for proportional scaling
   - Position wrapper to center content
   - Scale canvas internal buffers for sharp rendering

5. **Dimension Correction** (lines 673-723):
   - Verify actual viewport matches target
   - Correct for Chrome UI chrome if needed
   - Log dimension analysis

6. **Animation Triggering** (lines 725-859):
   - Force CSS animations to run
   - Trigger CreateJS/GSAP animations
   - Simulate hover states
   - Pause animations for frame control

7. **Frame Capture Loop** (lines 892-1016):
   - For each frame (0 to total_frames):
     - Set animation time using Web Animations API
     - Control CreateJS/GSAP timeline
     - Take screenshot
     - Validate dimensions
     - Save frame as PNG

8. **Cleanup** (lines 1017-1043):
   - Close browser
   - Return frames directory

**Animation Control**:
- Uses Web Animations API for CSS animations
- Direct time manipulation for CreateJS/GSAP
- Frame-perfect control via `currentTime` property

**Supported Animation Libraries**:
- CSS @keyframes
- CreateJS/EaselJS
- GSAP
- requestAnimationFrame-based animations

#### `encode_video(frames_dir, output_path, config, padding_info) -> bool`
**Location**: app.py:1045-1348

Encodes PNG frames to video using FFmpeg:

**Process**:
1. Validate frames exist
2. Read first frame to get dimensions
3. Build FFmpeg filter chain:
   - Scale (if needed)
   - Sharpen (unsharp filter)
   - Pad (if format conversion)
4. Execute FFmpeg with optimal settings
5. Fallback to baseline profile if encoding fails

**FFmpeg Command Structure**:
```bash
ffmpeg -y \
  -framerate {fps} \
  -i frame_%06d.png \
  -vf scale,unsharp,pad \
  -c:v libx264 \
  -pix_fmt yuv420p \
  -r {output_fps} \
  -crf 18 \
  -preset slow \
  -movflags +faststart \
  output.mp4
```

**Animation Speed Control**:
- Input FPS: Capture rate (e.g., 60 FPS)
- Output FPS: `input_fps × animation_speed`
- Example: 60 FPS capture × 0.85 speed = 51 FPS playback

#### `convert(zip_path, output_path, config) -> bool`
**Location**: app.py:1350-1402

Main pipeline orchestration:
1. Create temp directory
2. Extract ZIP
3. Render HTML to frames
4. Encode video
5. Cleanup temp files

---

## Streamlit UI Flow

**Location**: app.py:1405-1799

### Layout Structure

```
┌──────────────────────────────────────────┐
│          Main Title                      │
├──────────────────┬───────────────────────┤
│  Left Column     │  Right Column         │
│  (2/3 width)     │  (1/3 width)          │
├──────────────────┼───────────────────────┤
│ • File Upload    │ • Preview             │
│ • Settings       │ • Download Button     │
│ • Convert Button │                       │
│ • Debug Log      │                       │
└──────────────────┴───────────────────────┘
```

### User Flow

1. **Upload** (line 1569):
   - Accept .zip files only
   - Max 50MB file size
   - Validate ZIP format

2. **Analysis** (lines 1606-1633):
   - Auto-analyze HTML content
   - Detect dimensions, FPS, duration

3. **Settings** (lines 1641-1676):
   - Show detected values as metrics
   - Compact controls in expander:
     - Custom duration checkbox
     - Auto format vs manual selection

4. **Conversion** (lines 1697-1765):
   - Create VideoConfig
   - Setup progress indicators
   - Run converter with error handling
   - Show debug output in expander

5. **Results** (lines 1773-1794):
   - Display video preview
   - Provide download button
   - Cleanup temp files

### Theme Customization

**Location**: app.py:1414-1558

Dark mode with orange accent:
- Primary: `#ff8c42` (orange)
- Background: `#1a1a1a` (dark)
- Secondary: `#2d2d2d` (darker)
- Gradients for buttons and headers

---

## Configuration Files

### `requirements.txt`
**Purpose**: Python dependencies

```
streamlit>=1.31.0
selenium>=4.15.0
Pillow>=10.0.0
```

### `packages.txt`
**Purpose**: System dependencies for Streamlit Cloud

```
chromium
chromium-driver
ffmpeg
fonts-noto-color-emoji
fonts-liberation
fonts-dejavu-core
```

### `.streamlit/config.toml`
**Purpose**: Streamlit app configuration

```toml
[theme]
primaryColor="#ff8c42"
backgroundColor="#1a1a1a"
secondaryBackgroundColor="#2d2d2d"
textColor="#ffffff"

[server]
maxUploadSize = 50  # MB
enableXsrfProtection = false
enableCORS = false
```

---

## Key Technical Decisions

### 1. Why Selenium + Chrome?
- Renders HTML5 with full JavaScript support
- Accurate CSS animation capture
- Canvas and WebGL support
- CreateJS/GSAP compatibility

### 2. Why Frame-by-Frame Rendering?
- Precise animation control
- Consistent timing
- No dropped frames
- Frame-perfect synchronization

### 3. Why Web Animations API?
- Direct control over animation time
- Pause and seek capabilities
- Works with CSS @keyframes
- Better than requestAnimationFrame hacks

### 4. Why Proportional Scaling with Padding?
- No aspect ratio distortion
- Professional appearance
- Social media ready
- Preserves original design intent

### 5. Why CRF 18 + Slow Preset?
- High quality (CRF 18 = near-lossless)
- Reasonable file sizes
- Good compression efficiency
- Web-friendly

---

## Common Workflows

### Auto Conversion (Recommended)
1. User uploads HTML5 ZIP
2. Analyzer detects all parameters
3. FormatCSS selects optimal format
4. User clicks "Convert"
5. System renders and encodes
6. User downloads MP4

### Custom Duration
1. Follow auto conversion steps
2. Check "Custom duration"
3. Enter desired seconds
4. Continue conversion

### Manual Format Selection
1. Follow auto conversion steps
2. Uncheck "Auto format"
3. Select Square or Vertical
4. Continue conversion

---

## Performance Considerations

### Limits
- Max file size: 50MB (ZIP)
- Max uncompressed: 50MB
- Max files in ZIP: 1000
- Max processing: 4K @ 60fps @ 60s

### Optimization Strategies
1. **Capture Phase**:
   - Headless browser (no GUI overhead)
   - Controlled animation timing
   - Efficient screenshot capture

2. **Encoding Phase**:
   - Parallel FFmpeg filters
   - Hardware acceleration (if available)
   - Optimized preset selection

3. **Memory Management**:
   - Stream frames to disk
   - Clean temp files immediately
   - Use context managers

---

## Error Handling

### ZIP Extraction Errors
- Empty ZIP → ValueError
- Too many files → ValueError
- Path traversal → ValueError
- No HTML files → FileNotFoundError

### Rendering Errors
- Browser not found → FileNotFoundError
- Timeout → Selenium TimeoutException
- JavaScript errors → Logged, continue
- Dimension mismatch → Auto-correction

### Encoding Errors
- FFmpeg not found → FileNotFoundError
- Primary encoding fails → Fallback to baseline
- Fallback fails → Return False

### Debug Logging
All operations logged with timestamps:
```
[HH:MM:SS.mmm] Operation message
```

Accessible via "Debug Details" expander.

---

## Security Features

### ZIP Extraction
1. **Path Traversal Prevention**:
   - Normalize all paths
   - Block ".." and absolute paths

2. **ZIP Bomb Protection**:
   - Limit total files (1000)
   - Limit uncompressed size (50MB)

3. **File Size Limits**:
   - Upload: 50MB
   - Prevents DoS attacks

### Browser Sandboxing
- Headless mode (no GUI)
- No sandbox flag (for Docker/Cloud)
- Disabled dev tools
- Page load timeout (30s)
- Script timeout (10s)

---

## Deployment

### Local Development
```bash
pip install -r requirements.txt
streamlit run app.py
```

**Requirements**:
- Python 3.9+
- Chrome/Chromium browser
- FFmpeg installed

### Streamlit Cloud
1. Push to GitHub
2. Connect Streamlit Cloud
3. Select `app.py` as main file
4. Dependencies auto-installed from:
   - `requirements.txt` (Python)
   - `packages.txt` (System)

**Cloud Considerations**:
- Uses `chromium` instead of Chrome
- Uses `chromium-driver`
- FFmpeg from packages.txt
- Fonts for emoji support

---

## Debugging Guide

### Common Issues

#### "Browser not found"
**Cause**: Chrome/Chromium not installed
**Solution**: Install browser from `browser_paths` list (app.py:467)

#### "FFmpeg not found"
**Cause**: FFmpeg not in PATH
**Solution**: Install FFmpeg (`brew install ffmpeg`)

#### "Animation not captured"
**Cause**: Only hover effects, no timeline animations
**Solution**: Add CSS @keyframes or JS animations

#### "Video is stretched"
**Cause**: Format mismatch
**Solution**: Use "Auto format" mode

#### "Low quality video"
**Cause**: High compression
**Solution**: CRF is already 18 (near-lossless)

### Debug Output Analysis

**Key Sections to Check**:
1. `=== ZIP EXTRACTION ===`: File validation
2. `=== HTML5 TO VIDEO RENDERING ===`: Dimensions
3. `=== BROWSER INITIALIZATION ===`: Browser setup
4. `=== DIMENSION ANALYSIS ===`: Size verification
5. `=== ANIMATION SETUP ===`: Animation detection
6. `=== FRAME CAPTURE ===`: Rendering progress
7. `=== FFMPEG EXECUTION ===`: Encoding command

---

## Extension Points

### Adding New Animation Libraries

**Location**: app.py:725-859

Add detection and control in `animation_trigger_script`:
```javascript
if (typeof NewLibrary !== 'undefined') {
    console.log('NewLibrary detected');
    window.__newLibraryActive = true;
    // Initialize library
}
```

Then add timeline control in frame loop (app.py:916-961):
```javascript
if (typeof NewLibrary !== 'undefined') {
    NewLibrary.seek(elapsedSeconds);
}
```

### Adding New Output Formats

**Location**: app.py:166-186

Add format to `detect_best_format`:
```python
# 16:9 horizontal
horizontal_aspect = 16.0 / 9.0
diff_horizontal = abs(source_aspect - horizontal_aspect)

if diff_horizontal < min_diff:
    return (1920, 1080, "1920x1080 (Horizontal/YouTube)")
```

### Adding New Codecs

**Location**: app.py:1196-1209

Add codec-specific settings:
```python
elif config.codec == "libaom-av1":
    ffmpeg_cmd.extend(["-crf", str(config.crf)])
    ffmpeg_cmd.extend(["-cpu-used", "4"])
    self.log(f"Using AV1 codec with CRF")
```

---

## Testing Recommendations

### Test Cases

1. **Basic HTML**:
   - Simple static page
   - Expected: 10s video of static content

2. **CSS Animations**:
   - @keyframes animations
   - Expected: Smooth animation capture

3. **CreateJS Content**:
   - Banner ad with CreateJS
   - Expected: Timeline animations work

4. **GSAP Content**:
   - Modern animation framework
   - Expected: Smooth playback

5. **Format Conversion**:
   - Horizontal content → Square
   - Expected: Letterbox padding

6. **Large Files**:
   - 49MB ZIP file
   - Expected: Success

7. **Malicious ZIP**:
   - Path traversal attempt
   - Expected: ValueError

### Performance Benchmarks

**Typical Conversion**:
- 1080x1080, 60 FPS, 10s
- 600 frames total
- Capture: ~60s
- Encode: ~30s
- Total: ~90s

**High-End Conversion**:
- 1920x1080, 60 FPS, 60s
- 3600 frames total
- Capture: ~6 minutes
- Encode: ~3 minutes
- Total: ~9 minutes

---

## Code Quality

### Best Practices Implemented

1. **Type Hints**: VideoConfig dataclass
2. **Docstrings**: All public methods
3. **Error Handling**: Try-except with logging
4. **Security**: Input validation
5. **Logging**: Comprehensive debug output
6. **Cleanup**: Always cleanup temp files
7. **Progress**: User feedback via callbacks

### Code Organization

- **Lines 1-35**: Data structures
- **Lines 37-290**: Analysis and formatting
- **Lines 293-1403**: Core converter
- **Lines 1405-1799**: Streamlit UI

### Maintainability

- **Single Responsibility**: Each class has one job
- **Dependency Injection**: Progress callback
- **Configuration Objects**: VideoConfig
- **Clear Naming**: Descriptive method names
- **Comments**: Explain complex logic

---

## Future Enhancements (Not Implemented)

### Potential Features

1. **Multi-file Output**:
   - Generate multiple formats in one pass
   - Batch processing

2. **Advanced Upscaling**:
   - AI-based super-resolution
   - waifu2x integration

3. **Audio Support**:
   - Capture audio from HTML5 videos
   - Background music overlay

4. **Custom Watermarks**:
   - Add logo/text overlay
   - Timestamp display

5. **Progress Streaming**:
   - Real-time frame preview
   - Live encoding stats

6. **Cloud Storage**:
   - Direct upload to S3/GCS
   - Webhook notifications

---

## Troubleshooting Checklist

### Before Running
- [ ] Python 3.9+ installed
- [ ] Chrome/Chromium installed
- [ ] FFmpeg installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)

### Common Errors
- [ ] Check browser paths (app.py:467-474)
- [ ] Verify FFmpeg in PATH (`ffmpeg -version`)
- [ ] Check file permissions on temp directory
- [ ] Verify port 8501 available (Streamlit)

### Debug Steps
1. Enable debug output expander
2. Check "=== ERROR ===" sections
3. Verify dimensions match expectations
4. Test FFmpeg command manually
5. Check browser console logs

---

## API Reference

### HTML5Analyzer
```python
analyzer = HTML5Analyzer()
result = analyzer.analyze_html(html_path)
# Returns: {'width': int, 'height': int, 'duration': int, 'fps': int, 'detected': bool}
```

### FormatCSS
```python
width, height, name = FormatCSS.detect_best_format(source_w, source_h)
css = FormatCSS.generate_css(target_w, target_h, source_w, source_h, bg_color)
```

### SmartUpscaler
```python
dims = SmartUpscaler.calculate_fit_dimensions(src_w, src_h, tgt_w, tgt_h)
filter_str = SmartUpscaler.get_ffmpeg_scale_filter(src_w, src_h, tgt_w, tgt_h)
```

### HTML5ToVideoConverter
```python
def progress_callback(value: float, message: str):
    print(f"{value:.0%}: {message}")

converter = HTML5ToVideoConverter(progress_callback=progress_callback)
config = VideoConfig(width=1920, height=1080, fps=60, duration=10)
success = converter.convert(zip_path, output_path, config)
debug_log = converter.get_debug_output()
```

---

## Version History

### v3 (Current - OFICIAL-BACKUP-V3)
- Streamlit-based web UI
- Auto-detection of parameters
- Social media format conversion
- Comprehensive debug logging
- Security hardening

### v2 (OFICIAL-BACKUP-V2)
- Added format conversion
- Improved animation handling

### v1 (Earlier)
- Basic HTML to video conversion
- Manual parameter input only

---

## License
MIT License - See LICENSE file

---

## Support
For issues and questions:
1. Check debug output
2. Review this guide
3. Check GitHub issues
4. Create new issue with debug log

---

**Last Updated**: v3 (OFICIAL-BACKUP-V3)
**Total Lines of Code**: ~1800
**Primary Language**: Python
**Framework**: Streamlit
