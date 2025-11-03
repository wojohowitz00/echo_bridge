# Virtual Keyboard App - Agent System Guide

This document explains how to coordinate with the three specialized agents to build the Virtual Keyboard iOS app.

## Quick Start

### 1. Summon the Vision Processing Specialist
```bash
/summon-vision implement-hand-detector
```

This agent handles:
- Hand detection using HSV color segmentation
- Fingertip extraction via contour analysis
- Shadow-based touch detection
- Performance optimization (15+ fps, 95%+ accuracy)

### 2. Summon the iOS/SwiftUI Expert
Request via:
```bash
# Once vision pipeline is ready:
Work on camera integration and UI
```

This agent handles:
- SwiftUI views and layout
- AVFoundation camera management
- Real-time state management with Combine
- Visual feedback and debug overlay

### 3. Summon the Integration & Testing Agent
Request via:
```bash
/benchmark vision --device
```

This agent handles:
- Unit and integration testing
- Accuracy benchmarking (target: 95%)
- Performance profiling (target: 15+ fps)
- Comparison to paper specifications

## Agent Instructions

### Vision Processing Specialist
📍 **File**: `.claude/agents/vision-specialist-instructions.md`

**Key Responsibility**: Implement the computer vision pipeline that detects hands, extracts fingertips, analyzes shadows, and validates touches.

**Key Files**:
- `Sources/Vision/HandDetector.swift` - HSV color segmentation
- `Sources/Vision/FingertipDetector.swift` - Law of cosines
- `Sources/Vision/ShadowAnalyzer.swift` - Frame differencing
- `Sources/Vision/TouchValidator.swift` - Touch validation
- `Sources/Vision/VisionPipelineManager.swift` - Orchestrator

**Skill Reference**: `.claude/skills/virtual-keyboard-vision.md`

**Success Metrics**:
- Frame Rate: ≥15 fps on device
- Touch Accuracy: ≥95%
- Latency: <100ms
- Memory: <150MB

### iOS/SwiftUI Expert
📍 **File**: `.claude/agents/ios-expert-instructions.md`

**Key Responsibility**: Build the user interface, manage camera access, and ensure smooth real-time performance.

**Key Files**:
- `Sources/App.swift` - App entry point
- `Sources/UI/ContentView.swift` - Main coordinator
- `Sources/UI/CameraView.swift` - Camera feed
- `Sources/UI/KeyboardView.swift` - Keyboard layout
- `Sources/Core/CameraManager.swift` - Camera management

**Skill Reference**: `.claude/skills/ios-keyboard-layout.md` and `apple-intelligence-integration.md`

**Success Metrics**:
- 60fps UI rendering
- <50ms touch feedback latency
- Smooth camera integration
- Intuitive user experience

### Integration & Testing Agent
📍 **File**: `.claude/agents/integration-testing-instructions.md`

**Key Responsibility**: Validate accuracy, benchmark performance, and ensure all components work together.

**Key Tests**:
- Unit tests for vision components
- Integration tests for full pipeline
- Accuracy benchmarking (100+ test cases)
- Performance profiling

**Skill References**: All three skills contain testing guidance

**Success Metrics**:
- ≥95% accuracy on test dataset
- ≥15 fps sustained on device
- <100ms end-to-end latency
- Zero crashes in extended use

## Work Phases

### Phase 1: Core Vision Pipeline (Week 1)
```
Vision Specialist:
├─ HandDetector with HSV segmentation ✅
├─ FingertipDetector with law of cosines ✅
├─ ShadowAnalyzer with frame differencing ✅
└─ VisionPipelineManager integration ✅

Testing Agent:
└─ Unit tests for vision components
```

### Phase 2: iOS UI & Integration (Week 2)
```
iOS Expert:
├─ App.swift entry point ✅
├─ Camera management ✅
├─ ContentView & Camera feeds ✅
├─ KeyboardView & visualization ✅
└─ Real-time state management

Vision Specialist:
└─ Performance optimization

Testing Agent:
├─ Integration tests
└─ End-to-end validation
```

### Phase 3: Optimization & Testing (Week 3)
```
Testing Agent:
├─ Accuracy benchmarking (95%+ target)
├─ Performance profiling (15+ fps)
├─ Device testing
└─ Comparison to papers

Vision & iOS Specialists:
└─ Refinements based on results
```

## Custom Commands

### Build & Test
```bash
/build-test --quick          # Quick build + tests
/build-test --coverage       # Full suite with coverage
/build-test --device         # Test on physical device
```

### Benchmarking
```bash
/benchmark vision            # Vision pipeline
/benchmark accuracy          # Touch accuracy
/benchmark full --device     # Complete system
```

### Summon Specialist
```bash
/summon-vision implement-hand-detector      # Start implementation
/summon-vision optimize-performance         # Profile & optimize
/summon-vision review-accuracy              # Review results
```

## File Structure

```
VirtualKeyboardApp/
├── .claude/
│   ├── claude.md                          # Project context
│   ├── agents/
│   │   ├── vision-specialist-instructions.md
│   │   ├── ios-expert-instructions.md
│   │   └── integration-testing-instructions.md
│   ├── skills/
│   │   ├── virtual-keyboard-vision.md
│   │   ├── ios-keyboard-layout.md
│   │   └── apple-intelligence-integration.md
│   ├── mcp/
│   │   └── xcode-integration.md
│   └── commands/
│       ├── build-test.md
│       ├── benchmark.md
│       └── summon-vision.md
├── Sources/
│   ├── App.swift                          # Entry point ✅
│   ├── Vision/                            # Vision pipeline
│   │   ├── VisionPipelineManager.swift    # Orchestrator ✅
│   │   ├── HandDetector.swift             # (needs enhancement)
│   │   ├── FingertipDetector.swift        # (needs enhancement)
│   │   ├── ShadowAnalyzer.swift           # (needs enhancement)
│   │   └── TouchValidator.swift           # (needs enhancement)
│   ├── UI/
│   │   └── ContentView.swift              # Main view ✅
│   ├── Core/
│   │   └── CameraManager.swift            # (to implement)
│   └── Models/
│       ├── HandData.swift                 # ✅
│       ├── TouchEvent.swift               # ✅
│       └── KeyboardKey.swift              # ✅
├── Tests/
│   └── VisionTests/                       # (to implement)
├── Package.swift                           # ✅
└── AGENTS.md                              # (this file)
```

## Data Flow

```
Camera Frame (30fps)
    ↓
VisionPipelineManager
    ├→ HandDetector (HSV segmentation)
    │   └→ Hand ROI + confidence
    │
    ├→ FingertipDetector (Canny + law of cosines)
    │   └→ Fingertip (x_sf, y_sf)
    │
    ├→ ShadowAnalyzer (frame differencing)
    │   └→ Shadow tip (x_s, y_s)
    │
    └→ TouchValidator (distance + key mapping)
        └→ TouchEvent (if d < 1.0px)
            ↓
        InputStateManager
            ↓
        KeyPressEvent → Text Input
```

## Paper References

### Posner et al. (2012)
File: `Asinglecamerabasedfloatingvirtualkeyboardwithimprovedtouchdetection.pdf`

Key sections for implementation:
- **Section III**: Hand detection and preprocessing
- **Section IV**: Shadow-based touch detection
- **Distance formula**: d = √[(x_sf - x_s)² + (y_sf - y_s)²]
- **Touch threshold**: d < 1.0 pixel
- **Target accuracy**: 95%

### Borade et al. (2016)
File: `Paper_Keyboard_Using_Image_Processing.pdf`

Key sections:
- Edge detection (Canny)
- Contour analysis
- Hand segmentation
- Morphological operations

## Communication Tips

When requesting work from agents:

✅ **Good**:
```
/summon-vision implement-hand-detector

Goal: Implement HSV color segmentation for hand detection with proper morphological operations.
Reference: Section III of Posner et al. (2012)
Target: >0.7 detection confidence on test images
```

❌ **Vague**:
```
/summon-vision implement-hand-detector
```

## Success Criteria Checklist

- [ ] Vision pipeline detects hands reliably (>70% confidence)
- [ ] Fingertip detection accurate (<1px error)
- [ ] Shadow detection working with frame differencing
- [ ] Touch validation: distance < 1.0px = touch
- [ ] 15+ fps on iPhone 12+
- [ ] 95%+ accuracy on test dataset
- [ ] <100ms end-to-end latency
- [ ] <150MB memory usage
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] No crashes in extended use

## Next Steps

1. **Start Vision Implementation**:
   ```bash
   /summon-vision implement-hand-detector
   ```

2. **Once vision pipeline is working**:
   - iOS Expert starts camera integration
   - Testing Agent validates accuracy

3. **During optimization phase**:
   - All agents work on refinements
   - Testing Agent identifies bottlenecks

## Questions?

Refer to:
- `.claude/claude.md` for project context
- Relevant skill files for implementation details
- Agent instruction files for specific responsibilities
- Paper PDFs for algorithm details

Good luck! 🚀
