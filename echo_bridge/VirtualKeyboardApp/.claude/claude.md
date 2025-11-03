# Virtual Keyboard iOS App - Project Context

## Project Overview
Building a vision-based virtual keyboard iOS app using Swift and Apple Intelligence's Vision framework. The app enables real-time hand tracking and touch detection on any surface using a camera.

## Vision Pipeline Specification

### Core Objective
- Real-time hand detection and fingertip tracking
- Shadow-based touch detection for keyboard input
- 95% touch accuracy with <1-pixel distance threshold
- 15+ fps minimum frame rate
- On-device processing only (no cloud)

### Referenced Research Papers
1. **Posner et al. (2012)**: "A Single Camera Based Floating Virtual Keyboard with Improved Touch Detection"
   - Shadow analysis approach for distinguishing touch vs hover
   - Distance calculation: d = √[(x_sf - x_s)² + (y_sf - y_s)²]
   - Touch threshold: d < 1.0 pixel
   - File: `Asinglecamerabasedfloatingvirtualkeyboardwithimprovedtouchdetection.pdf`

2. **Borade et al. (2016)**: "Paper Keyboard Using Image Processing"
   - Image processing and morphological operations for hand detection
   - Edge detection (Canny) and contour analysis
   - Hand segmentation techniques
   - File: `Paper_Keyboard_Using_Image_Processing.pdf`

## Swift Architecture

### Design Patterns
- **MVVM** with Combine for reactive state management
- **SwiftUI** for UI components
- **AVFoundation** for camera management
- **Vision framework** for image processing

### Code Organization
- One struct/class per file
- Maximum 300 lines per file for maintainability
- Separation of concerns: Vision, UI, Core logic, Models

### File Structure
```
VirtualKeyboardApp/
├── .claude/
│   ├── claude.md (this file)
│   ├── skills/
│   │   ├── virtual-keyboard-vision.md
│   │   ├── ios-keyboard-layout.md
│   │   └── apple-intelligence-integration.md
│   ├── commands/
│   └── mcp/
├── Sources/
│   ├── Vision/
│   │   ├── VisionPipelineManager.swift
│   │   ├── HandDetector.swift
│   │   ├── FingertipDetector.swift
│   │   ├── ShadowAnalyzer.swift
│   │   └── TouchValidator.swift
│   ├── UI/
│   │   ├── ContentView.swift
│   │   ├── CameraView.swift
│   │   ├── KeyboardView.swift
│   │   └── DebugOverlayView.swift
│   ├── Core/
│   │   ├── CameraManager.swift
│   │   └── PerformanceMonitor.swift
│   └── Models/
│       ├── HandData.swift
│       ├── TouchEvent.swift
│       └── KeyboardKey.swift
```

## Key Constraints

### Performance Requirements
- **Frame Rate**: 15+ fps minimum (30+ fps target)
- **Latency**: <100ms end-to-end (camera to keyboard response)
- **Memory**: Optimize for iPhone memory constraints
- **CPU**: Process on background queue to avoid UI blocking

### Vision Processing
- **Camera Format**: 640x480 recommended (test 1280x720 on device)
- **Lighting**: Handle variable lighting conditions
- **ISO Setting**: Start with ISO 100 (from papers)
- **Reference Frame**: Capture calibration image for background subtraction

### Platform Support
- **iOS**: 14.0+
- **Form Factors**: iPhone and iPad optimization
- **Camera**: Rear-facing camera recommended for better hand tracking

## Touch Detection Algorithm (from papers)

### Step 1: Hand Detection
- Input: Live CMSampleBuffer from camera
- Color segmentation in HSV space (skin tone detection)
- Morphological operations (erode/dilate) for noise reduction
- Output: ROI (region of interest) containing hand

### Step 2: Fingertip Extraction
- Edge detection (Canny) on hand ROI
- Contour analysis using law of cosines
- Find point with smallest angle (fingertip)
- Output: Fingertip coordinates (x_sf, y_sf)

### Step 3: Shadow Analysis
- Subtract reference frame from current frame
- Apply same hand detection pipeline to shadow
- Output: Shadow tip coordinates (x_s, y_s)

### Step 4: Touch Validation
- Calculate distance: d = √[(x_sf - x_s)² + (y_sf - y_s)²]
- Touch detected if: d < 1.0 pixel (threshold from papers)
- Additional check: Both fingertip and shadow in same keyboard key region
- Target accuracy: 95%+

## Development Priorities

1. **Phase 1: Core Vision Pipeline**
   - Camera management and frame capture
   - Hand detection with basic color segmentation
   - Fingertip detection via contour analysis
   - Basic shadow analysis

2. **Phase 2: Touch Detection & Validation**
   - Implement shadow-based touch detection
   - Keyboard key mapping
   - Touch accuracy validation and testing

3. **Phase 3: UI & User Experience**
   - Keyboard layout visualization
   - Real-time debug overlay
   - Performance monitoring display
   - User feedback mechanisms

4. **Phase 4: Optimization & Testing**
   - Performance profiling and optimization
   - Multi-device testing (iPhone/iPad)
   - Accuracy benchmarking against 95% target
   - Battery and thermal optimization

## Testing Strategy

- Unit tests for vision pipeline components
- Integration tests for touch detection accuracy
- Performance tests for frame rate and latency
- Device testing on actual iPhone/iPad hardware
- Comparison against paper accuracy baselines

## References & Documentation
- Apple Vision Framework: https://developer.apple.com/documentation/vision
- AVFoundation Camera: https://developer.apple.com/documentation/avfoundation
- SwiftUI: https://developer.apple.com/documentation/swiftui
- Research Papers: See `/Papers/` directory in project root
