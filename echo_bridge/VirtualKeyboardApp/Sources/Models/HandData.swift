import Foundation
import CoreGraphics

/// Represents detected hand information from vision pipeline
struct HandData: Equatable {
    /// Fingertip coordinates in camera frame space
    let fingertipPosition: CGPoint

    /// Shadow fingertip coordinates in camera frame space
    let shadowTipPosition: CGPoint

    /// Euclidean distance between finger and shadow
    let fingerShadowDistance: Float

    /// Bounding box of hand region
    let handROI: CGRect

    /// Confidence score for hand detection (0.0 - 1.0)
    let detectionConfidence: Float

    /// Whether a valid hand was detected
    var isHandDetected: Bool {
        return detectionConfidence > 0.5
    }

    /// Whether touch is valid based on distance threshold
    var isTouchValid: Bool {
        return fingerShadowDistance < 1.0  // From Posner et al. (2012)
    }

    /// Touch confidence based on distance from threshold
    /// 1.0 when distance = 0, decreases as distance approaches threshold
    var touchConfidence: Float {
        let threshold: Float = 1.0
        return max(0.0, 1.0 - (fingerShadowDistance / threshold))
    }

    /// Timestamp of when this hand data was captured
    let timestamp: Date

    /// Frame number (for temporal tracking)
    let frameNumber: Int
}

/// Represents a hand detection request result
struct HandDetectionResult {
    enum Status {
        case success(HandData)
        case noHandDetected
        case lowConfidence(Float)
        case processingError(Error)
    }

    let status: Status
    let processingTime: TimeInterval
}

/// Extended hand tracking data with additional context
struct HandTrackingContext {
    /// Current hand data
    let current: HandData

    /// Previous frame's hand data (for motion tracking)
    let previous: HandData?

    /// Hand stability metric (0.0 - 1.0)
    /// Higher values indicate more stable tracking
    var stabilityScore: Float {
        guard let prev = previous else { return 0.5 }

        // Calculate position delta
        let positionDelta = hypot(
            current.fingertipPosition.x - prev.fingertipPosition.x,
            current.fingertipPosition.y - prev.fingertipPosition.y
        )

        // Normalize to 0-1 (positions within 50px are considered stable)
        let maxDelta: CGFloat = 50
        let normalizedDelta = min(1.0, positionDelta / maxDelta)

        return Float(1.0 - normalizedDelta)
    }

    /// Motion vector from previous to current frame
    var motionVector: CGVector? {
        guard let prev = previous else { return nil }
        return CGVector(
            dx: current.fingertipPosition.x - prev.fingertipPosition.x,
            dy: current.fingertipPosition.y - prev.fingertipPosition.y
        )
    }

    /// Whether hand is moving quickly (potential gesture)
    func isMovingQuickly(threshold: CGFloat = 30) -> Bool {
        guard let motion = motionVector else { return false }
        let speed = hypot(motion.dx, motion.dy)
        return speed > threshold
    }
}
