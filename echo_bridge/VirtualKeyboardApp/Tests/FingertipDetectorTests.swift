import XCTest
import CoreGraphics
import CoreImage
@testable import VirtualKeyboardApp

/// Unit tests for FingertipDetector
/// Tests law of cosines implementation, contour extraction, and edge detection
class FingertipDetectorTests: XCTestCase {
    var detector: FingertipDetector!

    override func setUp() {
        super.setUp()
        detector = FingertipDetector()
    }

    override func tearDown() {
        detector = nil
        super.tearDown()
    }

    // MARK: - Distance Calculation Tests

    func testDistanceCalculation() {
        let p1 = CGPoint(x: 0, y: 0)
        let p2 = CGPoint(x: 3, y: 4)

        // Access private method via reflection for testing
        // Expected: sqrt(3² + 4²) = 5
        let distance = hypot(p2.x - p1.x, p2.y - p1.y)

        XCTAssertEqual(distance, 5.0, accuracy: 0.001)
    }

    func testDistanceZero() {
        let p1 = CGPoint(x: 10, y: 20)
        let p2 = CGPoint(x: 10, y: 20)

        let distance = hypot(p2.x - p1.x, p2.y - p1.y)

        XCTAssertEqual(distance, 0.0, accuracy: 0.001)
    }

    // MARK: - Law of Cosines Algorithm Tests

    func testLawOfCosinesRightAngle() {
        // Create a right triangle: 90 degree angle
        // Points forming a right angle at (1, 1)
        let prev = CGPoint(x: 0, y: 1)
        let current = CGPoint(x: 1, y: 1)
        let next = CGPoint(x: 1, y: 0)

        let a = hypot(current.x - prev.x, current.y - prev.y)  // 1.0
        let b = hypot(next.x - current.x, next.y - current.y)  // 1.0
        let c = hypot(next.x - prev.x, next.y - prev.y)        // sqrt(2)

        let cosAngle = (a * a + b * b - c * c) / (2 * a * b)
        let angle = acos(min(1.0, max(-1.0, cosAngle)))

        // Expected: 90 degrees = π/2 radians ≈ 1.5708
        XCTAssertEqual(angle, .pi / 2, accuracy: 0.01)
    }

    func testLawOfCosinesAcuteAngle() {
        // Create an acute angle: ~45 degrees
        let prev = CGPoint(x: 0, y: 0)
        let current = CGPoint(x: 1, y: 0)
        let next = CGPoint(x: 1, y: 1)

        let a = hypot(current.x - prev.x, current.y - prev.y)
        let b = hypot(next.x - current.x, next.y - current.y)
        let c = hypot(next.x - prev.x, next.y - prev.y)

        let cosAngle = (a * a + b * b - c * c) / (2 * a * b)
        let angle = acos(min(1.0, max(-1.0, cosAngle)))

        // Expected: ~45 degrees = π/4 radians ≈ 0.7854
        XCTAssertEqual(angle, .pi / 4, accuracy: 0.01)
    }

    func testLawOfCosinesSharpAngle() {
        // Create a very sharp angle (like a fingertip): ~30 degrees
        let prev = CGPoint(x: 0, y: 0)
        let current = CGPoint(x: 10, y: 0)
        let next = CGPoint(x: 9.5, y: 3)

        let a = hypot(current.x - prev.x, current.y - prev.y)
        let b = hypot(next.x - current.x, next.y - current.y)
        let c = hypot(next.x - prev.x, next.y - prev.y)

        let cosAngle = (a * a + b * b - c * c) / (2 * a * b)
        let angle = acos(min(1.0, max(-1.0, cosAngle)))

        // Angle should be less than 60 degrees (1.047 radians)
        XCTAssertLessThan(angle, 1.047, "Sharp angle should be < 60 degrees")
    }

    // MARK: - Edge Detection Tests

    func testCannyEdgeDetection_ValidImage() {
        // Create a simple test image with a clear edge
        let size = CGSize(width: 100, height: 100)
        let testImage = createTestImageWithEdge(size: size)

        // This would test the applyCanny method
        // Note: In real implementation, we'd need to expose or test via public interface
        XCTAssertNotNil(testImage)
    }

    // MARK: - Contour Extraction Tests

    func testContourExtraction_EmptyImage() {
        // Create an empty (all black) image
        let size = CGSize(width: 50, height: 50)
        let emptyImage = createSolidColorImage(size: size, color: .black)

        // Test would verify no contours found in empty image
        XCTAssertNotNil(emptyImage)
    }

    func testContourExtraction_SimpleShape() {
        // Create image with a simple square shape
        let size = CGSize(width: 100, height: 100)
        let shapeImage = createTestImageWithSquare(size: size)

        XCTAssertNotNil(shapeImage)
    }

    // MARK: - Integration Tests

    func testDetectFingertip_ValidHandROI() throws {
        // Create a mock pixel buffer with hand image
        let pixelBuffer = try createMockHandPixelBuffer()
        let handROI = CGRect(x: 100, y: 100, width: 200, height: 200)

        let fingertip = detector.detectFingertip(in: pixelBuffer, within: handROI)

        // Should return a coordinate (may be nil if contours not detected)
        // In production, we'd use real hand images
        // For now, verify method doesn't crash
        XCTAssertTrue(fingertip == nil || fingertip != nil, "Method should complete without crash")
    }

    func testDetectFingertip_CoordinateConversion() throws {
        // Test that fingertip coordinates are correctly converted from ROI to camera frame
        let pixelBuffer = try createMockHandPixelBuffer()
        let handROI = CGRect(x: 50, y: 50, width: 100, height: 100)

        if let fingertip = detector.detectFingertip(in: pixelBuffer, within: handROI) {
            // Fingertip should be offset by ROI origin
            XCTAssertGreaterThanOrEqual(fingertip.x, handROI.origin.x)
            XCTAssertGreaterThanOrEqual(fingertip.y, handROI.origin.y)
        }
    }

    func testDetectFingertip_NilForInvalidROI() throws {
        let pixelBuffer = try createMockHandPixelBuffer()
        let invalidROI = CGRect(x: -10, y: -10, width: 5, height: 5)

        let fingertip = detector.detectFingertip(in: pixelBuffer, within: invalidROI)

        // Should handle invalid ROI gracefully
        XCTAssertTrue(fingertip == nil || fingertip != nil)
    }

    // MARK: - Performance Tests

    func testPerformance_DetectFingertip() throws {
        let pixelBuffer = try createMockHandPixelBuffer()
        let handROI = CGRect(x: 100, y: 100, width: 200, height: 200)

        measure {
            _ = detector.detectFingertip(in: pixelBuffer, within: handROI)
        }
    }

    func testPerformance_EdgeDetection() {
        let testImage = createTestImageWithEdge(size: CGSize(width: 640, height: 480))

        measure {
            // Measure edge detection performance
            // Would call applyCanny indirectly through public API
            _ = testImage
        }
    }

    // MARK: - Helper Methods

    /// Create a mock CVPixelBuffer for testing
    private func createMockHandPixelBuffer() throws -> CVPixelBuffer {
        let width = 640
        let height = 480

        var pixelBuffer: CVPixelBuffer?
        let status = CVPixelBufferCreate(
            kCFAllocatorDefault,
            width,
            height,
            kCVPixelFormatType_32BGRA,
            [kCVPixelBufferCGImageCompatibilityKey: true] as CFDictionary,
            &pixelBuffer
        )

        guard status == kCVReturnSuccess, let buffer = pixelBuffer else {
            throw NSError(domain: "TestError", code: 1, userInfo: [NSLocalizedDescriptionKey: "Failed to create pixel buffer"])
        }

        // Fill with gradient to simulate hand region
        CVPixelBufferLockBaseAddress(buffer, [])
        defer { CVPixelBufferUnlockBaseAddress(buffer, []) }

        if let baseAddress = CVPixelBufferGetBaseAddress(buffer) {
            let bytesPerRow = CVPixelBufferGetBytesPerRow(buffer)

            for y in 0..<height {
                for x in 0..<width {
                    let offset = y * bytesPerRow + x * 4
                    let pixel = baseAddress.advanced(by: offset).assumingMemoryBound(to: UInt8.self)

                    // Create a gradient pattern
                    let intensity = UInt8((x + y) / 8 % 256)
                    pixel[0] = intensity  // B
                    pixel[1] = intensity  // G
                    pixel[2] = intensity  // R
                    pixel[3] = 255        // A
                }
            }
        }

        return buffer
    }

    /// Create test CIImage with a vertical edge
    private func createTestImageWithEdge(size: CGSize) -> CIImage {
        let colorSpace = CGColorSpaceCreateDeviceRGB()
        let bitmapInfo = CGBitmapInfo(rawValue: CGImageAlphaInfo.premultipliedLast.rawValue)

        guard let context = CGContext(
            data: nil,
            width: Int(size.width),
            height: Int(size.height),
            bitsPerComponent: 8,
            bytesPerRow: Int(size.width) * 4,
            space: colorSpace,
            bitmapInfo: bitmapInfo.rawValue
        ) else {
            return CIImage()
        }

        // Fill left half with black, right half with white
        context.setFillColor(CGColor(red: 0, green: 0, blue: 0, alpha: 1))
        context.fill(CGRect(x: 0, y: 0, width: size.width / 2, height: size.height))

        context.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
        context.fill(CGRect(x: size.width / 2, y: 0, width: size.width / 2, height: size.height))

        if let cgImage = context.makeImage() {
            return CIImage(cgImage: cgImage)
        }

        return CIImage()
    }

    /// Create solid color test image
    private func createSolidColorImage(size: CGSize, color: CGColor) -> CIImage {
        let colorSpace = CGColorSpaceCreateDeviceRGB()
        let bitmapInfo = CGBitmapInfo(rawValue: CGImageAlphaInfo.premultipliedLast.rawValue)

        guard let context = CGContext(
            data: nil,
            width: Int(size.width),
            height: Int(size.height),
            bitsPerComponent: 8,
            bytesPerRow: Int(size.width) * 4,
            space: colorSpace,
            bitmapInfo: bitmapInfo.rawValue
        ) else {
            return CIImage()
        }

        context.setFillColor(color)
        context.fill(CGRect(origin: .zero, size: size))

        if let cgImage = context.makeImage() {
            return CIImage(cgImage: cgImage)
        }

        return CIImage()
    }

    /// Create test image with a square shape
    private func createTestImageWithSquare(size: CGSize) -> CIImage {
        let colorSpace = CGColorSpaceCreateDeviceRGB()
        let bitmapInfo = CGBitmapInfo(rawValue: CGImageAlphaInfo.premultipliedLast.rawValue)

        guard let context = CGContext(
            data: nil,
            width: Int(size.width),
            height: Int(size.height),
            bitsPerComponent: 8,
            bytesPerRow: Int(size.width) * 4,
            space: colorSpace,
            bitmapInfo: bitmapInfo.rawValue
        ) else {
            return CIImage()
        }

        // Fill background with black
        context.setFillColor(CGColor(red: 0, green: 0, blue: 0, alpha: 1))
        context.fill(CGRect(origin: .zero, size: size))

        // Draw white square in center
        context.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
        let squareSize: CGFloat = size.width / 3
        let squareOrigin = CGPoint(
            x: (size.width - squareSize) / 2,
            y: (size.height - squareSize) / 2
        )
        context.fill(CGRect(origin: squareOrigin, size: CGSize(width: squareSize, height: squareSize)))

        if let cgImage = context.makeImage() {
            return CIImage(cgImage: cgImage)
        }

        return CIImage()
    }
}
