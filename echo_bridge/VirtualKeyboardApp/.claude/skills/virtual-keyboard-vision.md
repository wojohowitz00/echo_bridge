# Virtual Keyboard Vision Pipeline Skill

## Overview
This skill implements the complete camera-based hand tracking and shadow analysis pipeline for touch detection in the Virtual Keyboard iOS app. It guides implementation of the vision algorithms from the Posner et al. (2012) and Borade et al. (2016) papers.

## Architecture

### Components
1. **VisionPipelineManager**: Orchestrates entire vision processing pipeline
2. **HandDetector**: Detects hand regions using color segmentation
3. **FingertipDetector**: Extracts fingertip coordinates from hand ROI
4. **ShadowAnalyzer**: Analyzes hand shadow for touch detection
5. **TouchValidator**: Validates if touch occurred based on finger-shadow distance

### Processing Flow
```
CMSampleBuffer (Camera Frame)
    ↓
Hand Detection (HSV color segmentation)
    ↓
Hand ROI ──────────→ Fingertip Detection (Canny + contour analysis)
    ├─→ Fingertip coords (x_sf, y_sf)
    │
    └──→ Shadow Analysis (background subtraction)
         ├─→ Shadow ROI
         └─→ Shadow tip coords (x_s, y_s)
    ↓
Distance Calculation: d = √[(x_sf - x_s)² + (y_sf - y_s)²]
    ↓
Touch Validation (d < 1.0 pixel?)
    ├─→ YES: Check if in keyboard key region
    └─→ NO: Hover state
    ↓
TouchEvent (with key mapping)
```

## Key Algorithms

### 1. Hand Detection
**Input**: CMSampleBuffer from camera feed
**Output**: Binary mask and ROI of hand region

**Algorithm**:
```
1. Convert frame to HSV color space
2. Create range filters for skin tone detection
   - Hue range: 0-20, 335-360 (reddish skin tones)
   - Saturation range: 10-40 (skin saturation)
   - Value range: 60-255 (brightness)
3. Apply morphological operations:
   - Dilate (kernel 5x5): Connect nearby pixels
   - Erode (kernel 5x5): Remove noise
   - Dilate again: Smooth boundaries
4. Find contours in binary mask
5. Extract largest contour as hand region
6. Compute bounding box as ROI
```

**Implementation Notes**:
- Use `CIFilter` for color space conversion
- `vImageDilate_ARGB8888` for morphological operations
- Handle lighting variations by adjusting HSV ranges per session
- Consider Gaussian blur (kernel 5x5) pre-processing for noise reduction

### 2. Fingertip Detection
**Input**: Hand ROI (binary mask)
**Output**: (x_sf, y_sf) fingertip coordinates

**Algorithm** (from Borade et al. 2016):
```
1. Apply Canny edge detection to hand ROI
   - Low threshold: 50
   - High threshold: 150
   - Kernel size: 3
2. Extract contours from edges
3. For each contour point, calculate angle using law of cosines:
   angle = arccos((a² + b² - c²) / (2ab))
   where a, b, c are distances between consecutive points
4. Find point with minimum angle (sharpest point)
5. Refine using sub-pixel precision (if needed)
6. Return coordinates relative to original frame
```

**Implementation Notes**:
- Use Vision framework's `VNContourRequest`
- Or use OpenCV (via opencv-swift) for more control
- Law of cosines identifies fingertip as the "corner" point
- Store result as `CGPoint` with origin at frame top-left

### 3. Shadow Extraction
**Input**: Current frame and reference frame (captured at app launch)
**Output**: Binary mask of shadow region

**Algorithm**:
```
1. Calculate frame difference: |current_frame - reference_frame|
2. Apply threshold to identify shadow region
   - Threshold value: 30-50 (based on lighting)
3. Apply morphological operations (dilate, erode) for smoothing
4. Find largest contour in shadow mask
5. Apply same hand detection pipeline to shadow mask
6. Extract fingertip from shadow using same algorithm as Step 2
```

**Implementation Notes**:
- Capture reference frame during app initialization
- Re-capture if lighting conditions change significantly
- Use difference frame (not absolute difference for speed)
- Shadow will appear as dark region in difference image
- ISO 100 recommended (from papers) for consistent shadow visibility

### 4. Touch Detection & Validation
**Input**: Fingertip coords (x_sf, y_sf) and shadow coords (x_s, y_s)
**Output**: TouchEvent or nil (no touch)

**Algorithm** (from Posner et al. 2012):
```
1. Calculate Euclidean distance between finger and shadow:
   d = √[(x_sf - x_s)² + (y_sf - y_s)²]

2. Apply distance threshold:
   if d < 1.0 pixel:
       → Touch detected
   else:
       → Hover state (finger above surface)

3. Map touch point to keyboard key:
   a. Calculate normalized coordinates relative to keyboard area
   b. Find which key region contains (x_sf, y_sf)
   c. Verify shadow is also in same key region (for robustness)

4. Validate touch by checking:
   - Distance threshold (d < 1.0)
   - Key region containment (finger in key)
   - Shadow region containment (shadow in key)
   - Temporal consistency (same key for 2+ frames)
```

**Implementation Notes**:
- Distance threshold of 1.0 pixel from Posner et al. paper
- Consider smoothing with temporal filter (average last 3 frames)
- Use CGRect intersection for key region checking
- Add debouncing: require touch state for min 50ms before reporting
- Log distance values for accuracy benchmarking

## Integration with Vision Framework

### CMSampleBuffer Processing
```swift
// Example pattern for processing camera frames
func processCameraFrame(_ sampleBuffer: CMSampleBuffer) {
    // 1. Convert CMSampleBuffer to CVPixelBuffer
    guard let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }

    // 2. Create CIImage for Vision processing
    let ciImage = CIImage(cvPixelBuffer: pixelBuffer)

    // 3. Apply Vision requests
    let request = VNImageRequestHandler(ciImage: ciImage, options: [:])

    // 4. Process asynchronously on background queue
    DispatchQueue.global(qos: .userInitiated).async {
        do {
            try request.perform(/* vision requests */)
        } catch {
            // Handle vision processing errors
        }
    }
}
```

### Performance Optimization
- **Frame Skipping**: Process every Nth frame if needed (e.g., 1 in 2 for 30fps → 15fps processing)
- **Resolution**: Start with 640x480, optimize to 1280x720 if performance allows
- **CADisplayLink**: Sync vision processing with screen refresh rate
- **Background Queue**: Use `.userInitiated` QoS to avoid UI blocking
- **Memory**: Use autoreleasepool for frame cleanup in loop

## Testing & Validation

### Unit Test Strategy
1. **Hand Detection**: Test with known hand images at various angles/lighting
2. **Fingertip Detection**: Verify accuracy with ground-truth labeled images
3. **Shadow Analysis**: Test with controlled lighting setups
4. **Touch Detection**: Verify distance calculation accuracy

### Integration Testing
1. **End-to-End Pipeline**: Full camera to touch event flow
2. **Real-time Performance**: Measure frames processed per second
3. **Accuracy Benchmarking**: Compare against paper's 95% target
   - Test on 100+ touches across keyboard
   - Calculate true positive rate
   - Log false positives and false negatives

### Debug Visualization
- Overlay hand ROI on camera feed
- Show fingertip and shadow points
- Display distance metric in real-time
- Show keyboard key mapping
- Performance metrics (FPS, latency)

## References

### Papers
- **Posner et al. (2012)**: Section III-IV (Hand detection, shadow analysis)
  - Distance formula: d = √[(x_sf - x_s)² + (y_sf - y_s)²]
  - Touch threshold: d < 1.0 pixel

- **Borade et al. (2016)**: Hand segmentation, edge detection, contour analysis
  - Law of cosines for fingertip detection
  - Morphological operations for noise reduction

### Apple Documentation
- Vision Framework: https://developer.apple.com/documentation/vision
- AVFoundation Camera: https://developer.apple.com/documentation/avfoundation
- Core Image: https://developer.apple.com/documentation/coreimage
- CVPixelBuffer: https://developer.apple.com/documentation/corevideo

### Implementation Libraries
- Vision (native Apple framework - preferred)
- Core Image for image processing
- Metal Performance Shaders (if additional optimization needed)

## Checklist for Implementation

- [ ] VisionPipelineManager orchestrates all components
- [ ] HandDetector uses HSV color segmentation + morphological ops
- [ ] FingertipDetector implements law of cosines contour analysis
- [ ] ShadowAnalyzer handles background subtraction
- [ ] TouchValidator calculates distance metric correctly
- [ ] Performance meets 15+ fps target
- [ ] Accuracy benchmarked against 95% target
- [ ] Debug visualization implemented for testing
- [ ] Unit tests for each component
- [ ] Integration tests for full pipeline
- [ ] Lighting conditions handled robustly
- [ ] Memory optimized for real-time processing
