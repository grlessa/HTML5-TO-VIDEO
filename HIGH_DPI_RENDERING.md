# High-DPI Rendering Approach

## Problem Statement

HTML5 banner ads are designed with **fixed pixel dimensions** (e.g., 320x480) and are **NOT responsive**. Attempting to scale them to social media formats (1080x1080, 1080x1920) using CSS manipulation (zoom, transform, etc.) results in catastrophic layout failures:

- Text wrapping incorrectly
- Elements overlapping
- Vertical spacing broken
- No amount of CSS patching can fix non-responsive HTML

## Previous Approaches (FAILED)

### 1. FFmpeg Upscaling (Rejected)
- Render at native 320x480
- Use FFmpeg to upscale to 1080x1920
- **Result:** Blurry text, poor quality

### 2. CSS Zoom/Transform (Failed)
- Render browser at 1080x1920
- Use CSS zoom/transform to scale 320x480 content
- **Result:** Layout completely broken, text overlapping, sections misaligned

### 3. Aggressive CSS Overrides (Failed)
- Flexbox gap, extreme margins, forced positioning
- **Result:** Still broken, fundamental approach was flawed

## New Approach: High-DPI Rendering with device-scale-factor

### Core Concept

Use Chrome's `--force-device-scale-factor` flag to render at high DPI **without changing layout**.

### How It Works

1. **Browser Window:** Set to NATIVE dimensions (320x480)
2. **Device Scale Factor:** Set to calculated scale (e.g., 3.375x for 1080÷320)
3. **Layout:** Stays at 320x480 (unaffected)
4. **Rendering:** Happens at high-DPI (1080x1620)
5. **Screenshot:** Captures at high-DPI resolution (1080x1620)
6. **FFmpeg:** Pads to final format (1080x1920 with black bars)

### Example: 320x480 → 1080x1920

```
Source: 320x480
Target: 1080x1920

Scale calculation:
- Width scale: 1080 / 320 = 3.375x
- Height scale: 1920 / 480 = 4.0x
- Use minimum: 3.375x (to fit within target)

Browser setup:
- Window size: 320x480 (native)
- Device scale factor: 3.375x

Screenshot result:
- Size: 1080x1620 (320×3.375 × 480×3.375)
- Quality: High-DPI, crisp text and graphics
- Layout: Intact, no CSS manipulation needed

FFmpeg processing:
- Input: 1080x1620 frames
- Padding: Add 150px top + 150px bottom
- Output: 1080x1920 with black bars
```

## Implementation Details

### Chrome Options

```python
window_size = f'{config.width},{config.height}'  # e.g., 320,480
device_scale = target_width / config.width        # e.g., 3.375

chrome_options.add_argument(f'--window-size={window_size}')
chrome_options.add_argument(f'--force-device-scale-factor={device_scale}')
```

### Minimal CSS

Only minimal CSS reset needed (no complex manipulation):

```javascript
document.documentElement.style.margin = '0';
document.documentElement.style.padding = '0';
document.documentElement.style.overflow = 'hidden';

document.body.style.margin = '0';
document.body.style.padding = '0';
document.body.style.overflow = 'hidden';
```

### Screenshot Handling

```python
# Screenshot will be at high-DPI: native × device-scale-factor
# Example: 320x480 window × 3.375 = 1080x1620 screenshot
# Save as-is, let FFmpeg handle final padding
img.save(frame_path)
```

### FFmpeg Processing

```python
padding_info = {
    'source_width': int(config.width * device_scale),   # 1080
    'source_height': int(config.height * device_scale), # 1620
    'target_width': 1080,
    'target_height': 1920,
    'bg_color': '#000000'
}

# FFmpeg will scale (if needed) and pad to exact target dimensions
```

## Benefits

### ✅ High Quality
- Browser renders at high DPI natively
- Sharp text, crisp icons, clean graphics
- No post-processing blur

### ✅ Layout Intact
- HTML5 ad sees 320x480 viewport
- All layout calculations work correctly
- No text wrapping issues
- No element overlap

### ✅ Simple & Reliable
- No complex CSS manipulation
- No responsive redesign needed
- Works with ANY HTML5 ad
- No CSS patching required

### ✅ Fast
- Browser rendering same speed
- FFmpeg padding is instant
- No AI upscaling overhead

### ✅ Social Media Ready
- 1080x1080 (Square/Instagram)
- 1080x1920 (Vertical/Stories)
- Auto-detected based on source aspect ratio
- Letterboxing/Pillarboxing with detected background color

## Technical Advantages

### vs FFmpeg Upscaling
- **FFmpeg:** Scales pixels (blur/interpolation)
- **High-DPI:** Browser renders vectors/fonts at target resolution (sharp)

### vs CSS Manipulation
- **CSS:** Breaks layout of non-responsive HTML
- **High-DPI:** Layout unchanged, only rendering resolution increases

### vs AI Upscaling
- **AI:** Slow, requires GPU, large dependencies
- **High-DPI:** Fast, CPU-based, native browser feature

## Limitations

### Black Bars
- Content is fitted to maintain aspect ratio
- Black bars added (letterboxing/pillarboxing)
- **This is intentional** to avoid distortion

### Fixed Formats
- Currently supports 1080x1080 and 1080x1920
- Can easily add more formats if needed

### Not True 4K
- High-DPI rendering, not native 4K design
- Quality depends on source content quality
- Good enough for social media (will be compressed anyway)

## Testing

Test with common HTML5 banner sizes:

| Size | Aspect | Target | Scale | Result |
|------|--------|--------|-------|---------|
| 300x250 | 1.2:1 | 1080x1080 | 3.6x | Letterbox |
| 320x480 | 0.67:1 | 1080x1920 | 3.375x | Perfect fit |
| 728x90 | 8.09:1 | 1080x1920 | 21.3x | Extreme bars |
| 160x600 | 0.27:1 | 1080x1920 | 6.75x | Pillarbox |
| 970x250 | 3.88:1 | 1080x1080 | 1.11x | Letterbox |

### Verification Checklist

- ✓ Screenshot size matches expected (native × device-scale)
- ✓ Layout intact (no text wrap/overlap)
- ✓ High quality rendering (crisp text)
- ✓ FFmpeg pads to exact target dimensions
- ✓ Black bars symmetric
- ✓ Background color detected correctly
- ✓ Video plays correctly

## Summary

**Previous approach:**
- Try to make non-responsive HTML responsive with CSS hacks
- **Result:** Catastrophic layout failures

**New approach:**
- Render at native resolution with high device-scale-factor
- Let browser handle high-DPI rendering
- Let FFmpeg handle final padding
- **Result:** Perfect layout, high quality, simple and reliable

**Key insight:**
> You cannot make non-responsive HTML responsive with CSS manipulation. Instead, use browser's native high-DPI rendering capabilities.
