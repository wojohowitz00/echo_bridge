# iOS Keyboard Layout & Touch Mapping Skill

## Overview
This skill implements the keyboard layout system, coordinate mapping, and touch validation logic for mapping camera-detected finger touches to keyboard keys. It bridges the vision pipeline output to actual keyboard input.

## Keyboard Coordinate System

### Frame Coordinate Spaces
1. **Camera Frame Coordinates**: (0,0) at top-left, matches CMSampleBuffer dimensions
2. **UI Coordinates**: SwiftUI space, (0,0) at top-left of keyboard view
3. **Normalized Coordinates**: (0,0) to (1,0) range for layout flexibility

### Mapping Pipeline
```
Vision Output (Camera Frame)
    ↓
Scale/Rotate to UI Coordinates
    ↓
Normalize to Keyboard Space (0-1 range)
    ↓
Map to Key Region
    ↓
Validate & Report Touch
```

## Keyboard Layout Definition

### Standard QWERTY Layout
```swift
struct KeyboardLayout {
    // Rows for QWERTY keyboard
    let rows: [[KeyDefinition]]

    // Keyboard dimensions in camera frame
    let frameSize: CGSize  // e.g., 640x480
    let keyboardFrame: CGRect  // Visible keyboard area

    // Key dimensions
    let keyAspectRatio: CGFloat  // width/height ratio
    let keySpacing: CGFloat  // pixels between keys
}

struct KeyDefinition {
    let identifier: String  // "q", "w", "e", etc.
    let character: String   // display character
    let frame: CGRect       // position in normalized space (0-1)
    let alternates: [String]  // shifted variants
}
```

### QWERTY Row Layout (Normalized Coordinates)
```
Row 0 (Numbers): 1 2 3 4 5 6 7 8 9 0
Row 1 (QWERTY):  Q W E R T Y U I O P
Row 2 (ASDF):    A S D F G H J K L
Row 3 (ZXCV):    Z X C V B N M , .

Layout properties:
- Keyboard width: 90% of frame width (10% margin on sides)
- Keyboard height: 40% of frame height
- Key width: (keyboard_width - spacing*(columns-1)) / columns
- Key height: (keyboard_height - spacing*(rows-1)) / rows
- Spacing: ~2-4 pixels between keys
```

### Coordinate Calculation
```swift
// Convert camera frame coordinates to key region
func getKeyAtPosition(_ point: CGPoint, in layout: KeyboardLayout) -> KeyDefinition? {
    // 1. Check if point is within keyboard frame
    guard layout.keyboardFrame.contains(point) else { return nil }

    // 2. Calculate position relative to keyboard origin
    let relativeX = point.x - layout.keyboardFrame.origin.x
    let relativeY = point.y - layout.keyboardFrame.origin.y

    // 3. Find row and column based on key dimensions
    let keyWidth = layout.keyDimensions.width
    let keyHeight = layout.keyDimensions.height
    let spacing = layout.keySpacing
    let stride = keyWidth + spacing  // distance between key starts

    let column = Int(relativeX / stride)
    let row = Int(relativeY / stride)

    // 4. Validate row/column bounds
    guard row >= 0 && row < layout.rows.count else { return nil }
    guard column >= 0 && column < layout.rows[row].count else { return nil }

    // 5. Return the key definition
    return layout.rows[row][column]
}
```

## Touch Validation Logic

### Validation Criteria (from Posner et al. 2012)
1. **Distance Threshold**: d < 1.0 pixel (finger-shadow distance)
2. **Key Region Containment**: Finger point must be within key boundaries
3. **Shadow Validation**: Shadow point must be in same key region (robustness)
4. **Temporal Consistency**: Touch sustained for minimum duration
5. **No Rapid Bouncing**: Filter out noisy transitions between keys

### Validation Implementation
```swift
struct TouchValidationConfig {
    let distanceThreshold: Float = 1.0  // pixels
    let keyMargin: CGFloat = 2.0  // allow points slightly outside key
    let minTouchDuration: TimeInterval = 0.05  // 50ms
    let debounceFrames: Int = 2  // require touch in 2+ consecutive frames
}

func validateTouch(
    fingerPoint: CGPoint,
    shadowPoint: CGPoint,
    distanceValue: Float,
    targetKey: KeyDefinition,
    config: TouchValidationConfig
) -> ValidationResult {
    // Criterion 1: Distance threshold
    guard distanceValue < config.distanceThreshold else {
        return .hoverState(distance: distanceValue)
    }

    // Criterion 2: Finger in key region (with margin)
    let expandedKeyFrame = targetKey.frame.insetBy(dx: -config.keyMargin, dy: -config.keyMargin)
    guard expandedKeyFrame.contains(fingerPoint) else {
        return .outsideKey
    }

    // Criterion 3: Shadow validation
    guard targetKey.frame.contains(shadowPoint) else {
        return .shadowMismatch  // shadow in different key
    }

    return .touchValid(key: targetKey)
}
```

## Multi-Language Keyboard Support

### Layout Definition by Language
```swift
enum KeyboardLanguage {
    case english
    case spanish
    case french
    case german
    case arabic
    case chinese
    case custom(layout: KeyboardLayout)

    var layout: KeyboardLayout {
        switch self {
        case .english:
            return KeyboardLayouts.qwerty
        case .spanish:
            return KeyboardLayouts.qwerty  // Same layout, different characters
        case .french:
            return KeyboardLayouts.azerty
        case .german:
            return KeyboardLayouts.qwertz
        case .arabic:
            return KeyboardLayouts.arabic
        case .chinese:
            return KeyboardLayouts.pinyin
        case .custom(let layout):
            return layout
        }
    }
}
```

### Dynamic Layout Switching
- Store active layout in @Published property
- Update KeyboardView when layout changes
- Recalculate touch mapping immediately
- Preserve reference frame (don't reprocess camera feed)

## Visual Feedback System

### Touch Feedback Types
```swift
enum TouchFeedback {
    case hover(key: KeyDefinition)  // Finger near but not touching
    case touch(key: KeyDefinition)  // Valid touch detected
    case invalid(reason: String)    // Invalid touch (outside bounds, etc.)
}
```

### UI Feedback Implementation
```swift
// In KeyboardView:
// 1. Highlight active key
//    - Fill key with highlight color (opacity 0.3)
//    - Show key enlargement (slight scale increase)
//
// 2. Show touch indicator
//    - Circle at detected finger position
//    - Color: Green for touch, Yellow for hover, Red for invalid
//    - Size: 15-20px diameter
//
// 3. Distance meter (debug mode)
//    - Show numeric distance value
//    - Progress bar: 0 pixels (touch) to 5 pixels
//    - Red when > threshold
//
// 4. Key label highlighting
//    - Primary character in normal text
//    - Highlight candidate key in real-time
//    - Flash on successful registration
```

### Debug Overlay
```swift
struct DebugOverlay: View {
    @ObservedObject var visionModel: VisionPipelineManager

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("FPS: \(visionModel.fps)")
            Text("Distance: \(String(format: "%.2f", visionModel.currentDistance))")
            Text("Touch Valid: \(visionModel.isTouchValid)")
            Text("Key: \(visionModel.currentKey?.identifier ?? "none")")
            Text("Frame: \(visionModel.frameCount)")
        }
        .font(.caption)
        .padding(8)
        .background(Color.black.opacity(0.5))
        .foregroundColor(.white)
    }
}
```

## Key Mapping & Event Reporting

### Touch Event Generation
```swift
struct TouchEvent {
    let key: KeyDefinition
    let timestamp: Date
    let fingerPoint: CGPoint
    let shadowPoint: CGPoint
    let distance: Float
    let confidenceScore: Float  // 0-1 based on distance from threshold
}

struct KeyPressEvent {
    let character: String
    let key: KeyDefinition
    let timestamp: Date
    let isShifted: Bool
    let swipeVector: CGVector?  // for swipe input
}
```

### Event Publishing
```swift
class KeyboardEventPublisher: NSObject {
    @Published var lastKeyPressed: KeyPressEvent?
    @Published var currentHighlight: KeyDefinition?

    func reportTouch(_ event: TouchEvent) {
        // Update highlight immediately
        currentHighlight = event.key

        // Debounce rapid presses
        if shouldRegisterPress(event) {
            let keyPress = KeyPressEvent(
                character: event.key.character,
                key: event.key,
                timestamp: event.timestamp,
                isShifted: isShiftPressed
            )
            lastKeyPressed = keyPress

            // Forward to text input system
            handleKeyPress(keyPress)
        }
    }
}
```

## Calibration & Adaptation

### Initial Calibration
```swift
// On app launch:
// 1. Show calibration screen
// 2. Guide user to place hand in different positions
// 3. Capture reference frame for shadow detection
// 4. Estimate camera-to-surface distance
// 5. Auto-adjust HSV color ranges based on actual lighting
```

### Runtime Adaptation
```swift
// Monitor for:
// - Lighting changes (recapture reference frame)
// - Touch accuracy drift (recalibrate if < 80%)
// - Performance degradation (adjust resolution)
// - Shadow visibility issues (adjust ISO/aperture)
```

## Performance Considerations

### Optimization Strategies
1. **Caching**: Pre-compute key frame boundaries, don't recalculate per touch
2. **Early Exit**: Check distance threshold before key region containment
3. **Spatial Hashing**: For keyboards with many keys, use grid-based lookup
4. **Batch Updates**: Accumulate touch events and process in batches

### Memory Optimization
```swift
// Store only current frame + one previous frame
// Clear older reference frames periodically
// Use autoreleasepool for temporary image buffers
```

## Testing & Validation

### Test Scenarios
1. **Single Key Press**: Verify correct key detected for each position
2. **Adjacent Keys**: Ensure proper handling of touch near key boundaries
3. **Rapid Presses**: Test debouncing with quick successive touches
4. **Multi-language**: Verify layout switching and character mapping
5. **Edge Cases**: Fingers outside keyboard area, partial touches

### Accuracy Metrics
```swift
struct AccuracyMetrics {
    let totalTouches: Int
    let correctKeys: Int
    let missedTouches: Int
    let falseTouches: Int

    var accuracy: Float {
        return Float(correctKeys) / Float(totalTouches)
    }
}
```

## Integration Checklist

- [ ] KeyboardLayout struct defined with QWERTY coordinates
- [ ] Coordinate mapping functions implemented and tested
- [ ] TouchValidationConfig with all criteria
- [ ] Multi-language layout support
- [ ] Visual feedback system integrated with UI
- [ ] Debug overlay for development
- [ ] Touch event publishing system
- [ ] Calibration flow implemented
- [ ] Performance optimized (caching, early exit)
- [ ] Accuracy testing framework
- [ ] Edge case handling verified

## References

### Related Skills
- virtual-keyboard-vision.md: Vision pipeline output
- apple-intelligence-integration.md: UI integration patterns

### Documentation
- iOS Keyboard APIs: https://developer.apple.com/documentation/uikit/uikeyboard
- CGGeometry: https://developer.apple.com/documentation/corefoundation/cggeometry
- Touch Handling: https://developer.apple.com/documentation/uikit/uievent
