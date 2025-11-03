import Foundation
import CoreGraphics

/// Represents a touch detection event from the vision pipeline
struct TouchEvent: Equatable {
    /// Key that was touched
    let key: KeyboardKey

    /// Fingerprint coordinates in camera frame
    let fingerPoint: CGPoint

    /// Shadow tip coordinates in camera frame
    let shadowPoint: CGPoint

    /// Distance between finger and shadow
    let distance: Float

    /// Confidence score (0.0 - 1.0) based on distance from threshold
    let confidenceScore: Float

    /// Timestamp when touch was detected
    let timestamp: Date

    /// Frame number for diagnostics
    let frameNumber: Int

    /// Whether this is a validated touch (passed all checks)
    let isValidated: Bool
}

/// Represents a key press event for keyboard input
struct KeyPressEvent: Equatable {
    /// The character to input
    let character: String

    /// The key that was pressed
    let key: KeyboardKey

    /// Timestamp of the press
    let timestamp: Date

    /// Whether shift was applied (for capitals)
    let isShifted: Bool

    /// Optional swipe vector for gesture input
    let swipeVector: CGVector?

    /// Touch confidence at the time of registration
    let touchConfidence: Float
}

/// Represents touch input state machine
enum TouchInputState: Equatable {
    /// No contact
    case idle

    /// Finger hovering above surface
    case hovering(key: KeyboardKey, distance: Float)

    /// Valid touch detected
    case touching(key: KeyboardKey, distance: Float, confidence: Float)

    /// Invalid touch (outside keyboard area)
    case invalid(reason: String)

    /// Touch in progress but being debounced
    case debouncing(key: KeyboardKey, frames: Int)

    /// Computed property to get current key if any
    var currentKey: KeyboardKey? {
        switch self {
        case .hovering(let key, _), .touching(let key, _, _), .debouncing(let key, _):
            return key
        case .idle, .invalid:
            return nil
        }
    }

    /// Computed property to check if actively touching
    var isActiveTouching: Bool {
        if case .touching = self {
            return true
        }
        return false
    }
}

/// Configuration for touch validation
struct TouchValidationConfig {
    /// Distance threshold for touch detection (pixels)
    let distanceThreshold: Float = 1.0  // From Posner et al. (2012)

    /// Margin around key boundaries to account for finger size (pixels)
    let keyMargin: CGFloat = 2.0

    /// Minimum duration a touch must be held before registration (milliseconds)
    let minTouchDuration: TimeInterval = 0.05  // 50ms

    /// Number of consecutive frames required to validate touch
    let debounceFrames: Int = 2

    /// Minimum confidence score to accept touch
    let minConfidenceScore: Float = 0.5

    /// Maximum time gap between frames before resetting debounce counter (milliseconds)
    let maxFrameGap: TimeInterval = 0.1

    /// Whether to require shadow validation (both finger and shadow in same key)
    let requireShadowValidation: Bool = true
}

/// Result of touch validation
enum TouchValidationResult: Equatable {
    /// Touch is valid and ready to report
    case touchValid(TouchEvent)

    /// Finger hovering (not touching)
    case hoverState(distance: Float, key: KeyboardKey?)

    /// Invalid touch (outside keyboard area)
    case outsideKey

    /// Shadow validation failed
    case shadowMismatch

    /// Touch below confidence threshold
    case lowConfidence(Float)

    /// No valid key detected
    case noKeyDetected

    /// Computed property for error message
    var errorMessage: String? {
        switch self {
        case .outsideKey:
            return "Touch outside keyboard area"
        case .shadowMismatch:
            return "Finger and shadow in different keys"
        case .lowConfidence(let score):
            return "Touch confidence too low: \(String(format: "%.1f%%", score * 100))"
        case .noKeyDetected:
            return "No keyboard key detected at touch position"
        default:
            return nil
        }
    }
}

/// Statistics about touch input accuracy and performance
struct TouchStatistics: Equatable {
    /// Total number of touches attempted
    let totalTouches: Int

    /// Number of successful touches
    let successfulTouches: Int

    /// Number of missed touches (finger moved away)
    let missedTouches: Int

    /// Number of invalid/rejected touches
    let invalidTouches: Int

    /// Average touch confidence score
    let averageConfidence: Float

    /// Average time from hover to valid touch
    let averageHoverToTouchTime: TimeInterval

    /// Most commonly hit key
    let mostHitKey: KeyboardKey?

    /// Least commonly hit key
    let leastHitKey: KeyboardKey?

    /// Computed accuracy percentage
    var accuracyPercentage: Float {
        guard totalTouches > 0 else { return 0 }
        return Float(successfulTouches) / Float(totalTouches) * 100
    }

    /// Computed success rate (0.0 - 1.0)
    var successRate: Float {
        guard totalTouches > 0 else { return 0 }
        return Float(successfulTouches) / Float(totalTouches)
    }

    /// Whether accuracy meets target threshold
    var meetsAccuracyTarget: Bool {
        return accuracyPercentage >= 95.0  // Target from papers
    }
}
