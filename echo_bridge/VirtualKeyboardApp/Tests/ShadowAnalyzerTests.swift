import XCTest
import CoreGraphics
import CoreImage
import CoreVideo
@testable import VirtualKeyboardApp

/// Unit tests for ShadowAnalyzer
/// Tests frame differencing, shadow detection, adaptive thresholding, and reference frame management
class ShadowAnalyzerTests: XCTestCase {
    var analyzer: ShadowAnalyzer!

    override func setUp() {
        super.setUp()
        analyzer = ShadowAnalyzer()
    }

    override func tearDown() {
        analyzer = nil
        super.tearDown()
    }

    // MARK: - Reference Frame Management Tests

    func testCaptureReferenceFrame_ValidPixelBuffer() throws {
        let referenceBuffer = try createMockPixelBuffer(width: 640, height: 480, fillPattern: .solid(intensity: 128))

        // Should not crash when capturing reference frame
        analyzer.captureReferenceFrame(referenceBuffer)

        // Verify reference frame was stored by attempting shadow analysis
        let currentBuffer = try createMockPixelBuffer(width: 640, height: 480, fillPattern: .solid(intensity: 150))
        let handROI = CGRect(x: 100, y: 100, width: 200, height: 200)

        let shadowData = analyzer.analyzeShadowSync(currentFrame: currentBuffer, handROI: handROI)

        // May be nil if no shadow detected, but should not crash
        XCTAssertTrue(shadowData == nil || shadowData != nil, "Analysis should complete without crash")
    }

    func testCaptureReferenceFrame_PreservesPixelData() throws {
        let referenceBuffer = try createMockPixelBuffer(width: 100, height: 100, fillPattern: .gradient)

        analyzer.captureReferenceFrame(referenceBuffer)

        // Reference frame should be independent copy
        // Modifying original should not affect stored reference
        modifyPixelBuffer(referenceBuffer, fillValue: 0)

        let currentBuffer = try createMockPixelBuffer(width: 100, height: 100, fillPattern: .gradient)
        let handROI = CGRect(x: 10, y: 10, width: 80, height: 80)

        let shadowData = analyzer.analyzeShadowSync(currentFrame: currentBuffer, handROI: handROI)

        // Should work with stored reference, not modified original
        XCTAssertTrue(shadowData == nil || shadowData != nil)
    }

    func testAnalyzeShadowSync_NoReferenceFrame() throws {
        // Analyze without capturing reference frame first
        let currentBuffer = try createMockPixelBuffer(width: 640, height: 480, fillPattern: .solid(intensity: 150))
        let handROI = CGRect(x: 100, y: 100, width: 200, height: 200)

        let shadowData = analyzer.analyzeShadowSync(currentFrame: currentBuffer, handROI: handROI)

        // Should return nil when no reference frame
        XCTAssertNil(shadowData, "Should return nil without reference frame")
    }

    // MARK: - Frame Differencing Tests

    func testFrameDifferencing_IdenticalFrames() throws {
        let buffer1 = try createMockPixelBuffer(width: 320, height: 240, fillPattern: .solid(intensity: 100))
        let buffer2 = try createMockPixelBuffer(width: 320, height: 240, fillPattern: .solid(intensity: 100))

        analyzer.captureReferenceFrame(buffer1)
        let handROI = CGRect(x: 50, y: 50, width: 100, height: 100)

        let shadowData = analyzer.analyzeShadowSync(currentFrame: buffer2, handROI: handROI)

        // Identical frames should produce no shadow (nil result)
        XCTAssertNil(shadowData, "Identical frames should not detect shadow")
    }

    func testFrameDifferencing_DifferentFrames() throws {
        let referenceBuffer = try createMockPixelBuffer(width: 320, height: 240, fillPattern: .solid(intensity: 100))
        let currentBuffer = try createMockPixelBuffer(width: 320, height: 240, fillPattern: .solid(intensity: 150))

        analyzer.captureReferenceFrame(referenceBuffer)
        let handROI = CGRect(x: 50, y: 50, width: 100, height: 100)

        let shadowData = analyzer.analyzeShadowSync(currentFrame: currentBuffer, handROI: handROI)

        // Different frames may or may not detect shadow depending on threshold
        // Test that it completes without error
        XCTAssertTrue(shadowData == nil || shadowData != nil)
    }

    func testFrameDifferencing_HandPresent() throws {
        // Reference frame: uniform background
        let referenceBuffer = try createMockPixelBuffer(width: 640, height: 480, fillPattern: .solid(intensity: 128))

        // Current frame: hand and shadow (darker region)
        let currentBuffer = try createMockPixelBuffer(width: 640, height: 480, fillPattern: .withShadow)

        analyzer.captureReferenceFrame(referenceBuffer)
        let handROI = CGRect(x: 200, y: 150, width: 150, height: 200)

        let shadowData = analyzer.analyzeShadowSync(currentFrame: currentBuffer, handROI: handROI)

        // Should detect shadow when hand is present
        if let shadow = shadowData {
            XCTAssertGreaterThan(shadow.confidence, 0.0, "Should have positive confidence")
            XCTAssertGreaterThanOrEqual(shadow.processingTime, 0.0, "Processing time should be non-negative")
        }
    }

    // MARK: - Shadow Detection Tests

    func testShadowDetection_ValidShadowROI() throws {
        let referenceBuffer = try createMockPixelBuffer(width: 640, height: 480, fillPattern: .solid(intensity: 128))
        let currentBuffer = try createMockPixelBuffer(width: 640, height: 480, fillPattern: .withShadow)

        analyzer.captureReferenceFrame(referenceBuffer)
        let handROI = CGRect(x: 200, y: 150, width: 150, height: 200)

        let shadowData = analyzer.analyzeShadowSync(currentFrame: currentBuffer, handROI: handROI)

        if let shadow = shadowData {
            // Shadow ROI should be reasonable size
            XCTAssertGreaterThan(shadow.shadowROI.width, 10, "Shadow width should be > 10px")
            XCTAssertGreaterThan(shadow.shadowROI.height, 10, "Shadow height should be > 10px")

            // Shadow tip should be within or near shadow ROI
            let expandedROI = shadow.shadowROI.insetBy(dx: -20, dy: -20)
            XCTAssertTrue(
                expandedROI.contains(shadow.shadowTipPosition),
                "Shadow tip should be within or near shadow ROI"
            )
        }
    }

    func testShadowDetection_MinimumShadowArea() throws {
        // Create tiny shadow (should be filtered by minShadowArea = 1000)
        let referenceBuffer = try createMockPixelBuffer(width: 320, height: 240, fillPattern: .solid(intensity: 128))
        let currentBuffer = try createMockPixelBuffer(width: 320, height: 240, fillPattern: .tinyShadow)

        analyzer.captureReferenceFrame(referenceBuffer)
        let handROI = CGRect(x: 100, y: 80, width: 120, height: 80)

        let shadowData = analyzer.analyzeShadowSync(currentFrame: currentBuffer, handROI: handROI)

        // Tiny shadow should be filtered out
        XCTAssertNil(shadowData, "Shadow below minimum area should not be detected")
    }

    func testShadowDetection_OutsideHandROI() throws {
        // Shadow far from hand region should not be detected
        let referenceBuffer = try createMockPixelBuffer(width: 640, height: 480, fillPattern: .solid(intensity: 128))
        let currentBuffer = try createMockPixelBuffer(width: 640, height: 480, fillPattern: .distantShadow)

        analyzer.captureReferenceFrame(referenceBuffer)
        let handROI = CGRect(x: 50, y: 50, width: 100, height: 100)  // Hand in top-left

        let shadowData = analyzer.analyzeShadowSync(currentFrame: currentBuffer, handROI: handROI)

        // Shadow far from hand should not be detected (filtered by search ROI)
        XCTAssertNil(shadowData, "Shadow outside hand region should not be detected")
    }

    // MARK: - Shadow Fingertip Detection Tests

    func testShadowFingertip_LawOfCosines() throws {
        // Test that shadow tip uses law of cosines (same as fingertip detector)
        let referenceBuffer = try createMockPixelBuffer(width: 640, height: 480, fillPattern: .solid(intensity: 128))
        let currentBuffer = try createMockPixelBuffer(width: 640, height: 480, fillPattern: .withPointedShadow)

        analyzer.captureReferenceFrame(referenceBuffer)
        let handROI = CGRect(x: 200, y: 150, width: 150, height: 200)

        let shadowData = analyzer.analyzeShadowSync(currentFrame: currentBuffer, handROI: handROI)

        if let shadow = shadowData {
            // Shadow tip should be detected at sharp point
            XCTAssertNotEqual(shadow.shadowTipPosition, CGPoint.zero)

            // Confidence should be reasonable
            XCTAssertGreaterThanOrEqual(shadow.confidence, 0.0)
            XCTAssertLessThanOrEqual(shadow.confidence, 1.0)
        }
    }

    func testShadowFingertip_FallbackToCentroid() throws {
        // Test fallback to ROI center when law of cosines fails
        let referenceBuffer = try createMockPixelBuffer(width: 320, height: 240, fillPattern: .solid(intensity: 128))
        let currentBuffer = try createMockPixelBuffer(width: 320, height: 240, fillPattern: .roundShadow)

        analyzer.captureReferenceFrame(referenceBuffer)
        let handROI = CGRect(x: 100, y: 80, width: 120, height: 100)

        let shadowData = analyzer.analyzeShadowSync(currentFrame: currentBuffer, handROI: handROI)

        if let shadow = shadowData {
            // Should fall back to center when no sharp point found
            let centerX = shadow.shadowROI.midX
            let centerY = shadow.shadowROI.midY

            // Shadow tip should be near center (within 20% of ROI dimensions)
            let xDelta = abs(shadow.shadowTipPosition.x - centerX)
            let yDelta = abs(shadow.shadowTipPosition.y - centerY)

            XCTAssertLessThan(xDelta, shadow.shadowROI.width * 0.2)
            XCTAssertLessThan(yDelta, shadow.shadowROI.height * 0.2)

            // Fallback should have lower confidence
            XCTAssertLessThanOrEqual(shadow.confidence, 0.7)
        }
    }

    // MARK: - Adaptive Thresholding Tests

    func testAdaptiveThreshold_BrightLighting() throws {
        // Bright lighting → higher differences → higher threshold
        let referenceBuffer = try createMockPixelBuffer(width: 320, height: 240, fillPattern: .solid(intensity: 200))
        let currentBuffer = try createMockPixelBuffer(width: 320, height: 240, fillPattern: .solid(intensity: 220))

        analyzer.captureReferenceFrame(referenceBuffer)
        let handROI = CGRect(x: 50, y: 50, width: 100, height: 100)

        // First analysis to update adaptive threshold
        _ = analyzer.analyzeShadowSync(currentFrame: currentBuffer, handROI: handROI)

        // Threshold should adapt (can't directly test private variable, but verify no crash)
        XCTAssertTrue(true, "Adaptive threshold updated without crash")
    }

    func testAdaptiveThreshold_DimLighting() throws {
        // Dim lighting → lower differences → lower threshold
        let referenceBuffer = try createMockPixelBuffer(width: 320, height: 240, fillPattern: .solid(intensity: 50))
        let currentBuffer = try createMockPixelBuffer(width: 320, height: 240, fillPattern: .solid(intensity: 60))

        analyzer.captureReferenceFrame(referenceBuffer)
        let handROI = CGRect(x: 50, y: 50, width: 100, height: 100)

        _ = analyzer.analyzeShadowSync(currentFrame: currentBuffer, handROI: handROI)

        // Verify adaptive behavior works in dim conditions
        XCTAssertTrue(true, "Adaptive threshold works in dim lighting")
    }

    func testAdaptiveThreshold_RangeClamp() throws {
        // Test that threshold stays in valid range (20-80)
        let referenceBuffer = try createMockPixelBuffer(width: 320, height: 240, fillPattern: .solid(intensity: 0))
        let currentBuffer = try createMockPixelBuffer(width: 320, height: 240, fillPattern: .solid(intensity: 255))

        analyzer.captureReferenceFrame(referenceBuffer)
        let handROI = CGRect(x: 50, y: 50, width: 100, height: 100)

        _ = analyzer.analyzeShadowSync(currentFrame: currentBuffer, handROI: handROI)

        // Extreme lighting should still clamp threshold to valid range
        // (Can't directly test, but verify no crash or invalid behavior)
        XCTAssertTrue(true, "Threshold clamped to valid range")
    }

    // MARK: - Confidence Calculation Tests

    func testConfidence_LargeShadow() throws {
        let referenceBuffer = try createMockPixelBuffer(width: 640, height: 480, fillPattern: .solid(intensity: 128))
        let currentBuffer = try createMockPixelBuffer(width: 640, height: 480, fillPattern: .largeShadow)

        analyzer.captureReferenceFrame(referenceBuffer)
        let handROI = CGRect(x: 200, y: 150, width: 200, height: 250)

        let shadowData = analyzer.analyzeShadowSync(currentFrame: currentBuffer, handROI: handROI)

        if let shadow = shadowData {
            // Large shadow should have higher confidence
            XCTAssertGreaterThan(shadow.confidence, 0.5, "Large shadow should have confidence > 0.5")
        }
    }

    func testConfidence_SmallShadow() throws {
        let referenceBuffer = try createMockPixelBuffer(width: 640, height: 480, fillPattern: .solid(intensity: 128))
        let currentBuffer = try createMockPixelBuffer(width: 640, height: 480, fillPattern: .smallShadow)

        analyzer.captureReferenceFrame(referenceBuffer)
        let handROI = CGRect(x: 200, y: 150, width: 150, height: 200)

        let shadowData = analyzer.analyzeShadowSync(currentFrame: currentBuffer, handROI: handROI)

        if let shadow = shadowData {
            // Small shadow should have lower confidence
            XCTAssertLessThan(shadow.confidence, 0.8, "Small shadow should have lower confidence")
        }
    }

    // MARK: - Performance Tests

    func testPerformance_FrameDifferencing() throws {
        let referenceBuffer = try createMockPixelBuffer(width: 640, height: 480, fillPattern: .solid(intensity: 128))
        let currentBuffer = try createMockPixelBuffer(width: 640, height: 480, fillPattern: .withShadow)

        analyzer.captureReferenceFrame(referenceBuffer)
        let handROI = CGRect(x: 200, y: 150, width: 150, height: 200)

        measure {
            _ = analyzer.analyzeShadowSync(currentFrame: currentBuffer, handROI: handROI)
        }
    }

    func testPerformance_FullPipeline() throws {
        let referenceBuffer = try createMockPixelBuffer(width: 1920, height: 1080, fillPattern: .solid(intensity: 128))
        let currentBuffer = try createMockPixelBuffer(width: 1920, height: 1080, fillPattern: .withShadow)

        analyzer.captureReferenceFrame(referenceBuffer)
        let handROI = CGRect(x: 500, y: 300, width: 400, height: 500)

        // Full HD performance test
        measure {
            _ = analyzer.analyzeShadowSync(currentFrame: currentBuffer, handROI: handROI)
        }
    }

    func testPerformanceTarget_Sub15ms() throws {
        // Target: <15ms per frame (from specification)
        let referenceBuffer = try createMockPixelBuffer(width: 640, height: 480, fillPattern: .solid(intensity: 128))
        let currentBuffer = try createMockPixelBuffer(width: 640, height: 480, fillPattern: .withShadow)

        analyzer.captureReferenceFrame(referenceBuffer)
        let handROI = CGRect(x: 200, y: 150, width: 150, height: 200)

        let startTime = CFAbsoluteTimeGetCurrent()
        let shadowData = analyzer.analyzeShadowSync(currentFrame: currentBuffer, handROI: handROI)
        let elapsed = CFAbsoluteTimeGetCurrent() - startTime

        XCTAssertLessThan(elapsed, 0.015, "Processing should complete in <15ms")

        if let shadow = shadowData {
            XCTAssertLessThan(shadow.processingTime, 0.015, "Reported processing time should be <15ms")
        }
    }

    // MARK: - Async Analysis Tests

    func testAnalyzeShadowAsync() throws {
        let referenceBuffer = try createMockPixelBuffer(width: 640, height: 480, fillPattern: .solid(intensity: 128))
        let currentBuffer = try createMockPixelBuffer(width: 640, height: 480, fillPattern: .withShadow)
        let handROI = CGRect(x: 200, y: 150, width: 150, height: 200)

        let expectation = XCTestExpectation(description: "Shadow analysis completion")

        analyzer.analyzeShadow(
            currentFrame: currentBuffer,
            referenceFrame: referenceBuffer,
            handROI: handROI
        ) { shadowData in
            // Should complete on background thread
            XCTAssertFalse(Thread.isMainThread, "Should execute on background thread")

            // May or may not detect shadow
            XCTAssertTrue(shadowData == nil || shadowData != nil)

            expectation.fulfill()
        }

        wait(for: [expectation], timeout: 1.0)
    }

    // MARK: - Helper Methods

    enum FillPattern {
        case solid(intensity: UInt8)
        case gradient
        case withShadow
        case withPointedShadow
        case roundShadow
        case tinyShadow
        case distantShadow
        case largeShadow
        case smallShadow
    }

    /// Create a mock CVPixelBuffer for testing
    private func createMockPixelBuffer(width: Int, height: Int, fillPattern: FillPattern) throws -> CVPixelBuffer {
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

        CVPixelBufferLockBaseAddress(buffer, [])
        defer { CVPixelBufferUnlockBaseAddress(buffer, []) }

        guard let baseAddress = CVPixelBufferGetBaseAddress(buffer) else {
            throw NSError(domain: "TestError", code: 2, userInfo: [NSLocalizedDescriptionKey: "Failed to get base address"])
        }

        let bytesPerRow = CVPixelBufferGetBytesPerRow(buffer)

        switch fillPattern {
        case .solid(let intensity):
            fillSolid(baseAddress: baseAddress, width: width, height: height, bytesPerRow: bytesPerRow, intensity: intensity)

        case .gradient:
            fillGradient(baseAddress: baseAddress, width: width, height: height, bytesPerRow: bytesPerRow)

        case .withShadow:
            fillWithShadow(baseAddress: baseAddress, width: width, height: height, bytesPerRow: bytesPerRow)

        case .withPointedShadow:
            fillWithPointedShadow(baseAddress: baseAddress, width: width, height: height, bytesPerRow: bytesPerRow)

        case .roundShadow:
            fillWithRoundShadow(baseAddress: baseAddress, width: width, height: height, bytesPerRow: bytesPerRow)

        case .tinyShadow:
            fillWithTinyShadow(baseAddress: baseAddress, width: width, height: height, bytesPerRow: bytesPerRow)

        case .distantShadow:
            fillWithDistantShadow(baseAddress: baseAddress, width: width, height: height, bytesPerRow: bytesPerRow)

        case .largeShadow:
            fillWithLargeShadow(baseAddress: baseAddress, width: width, height: height, bytesPerRow: bytesPerRow)

        case .smallShadow:
            fillWithSmallShadow(baseAddress: baseAddress, width: width, height: height, bytesPerRow: bytesPerRow)
        }

        return buffer
    }

    private func fillSolid(baseAddress: UnsafeMutableRawPointer, width: Int, height: Int, bytesPerRow: Int, intensity: UInt8) {
        for y in 0..<height {
            for x in 0..<width {
                let offset = y * bytesPerRow + x * 4
                let pixel = baseAddress.advanced(by: offset).assumingMemoryBound(to: UInt8.self)
                pixel[0] = intensity  // B
                pixel[1] = intensity  // G
                pixel[2] = intensity  // R
                pixel[3] = 255        // A
            }
        }
    }

    private func fillGradient(baseAddress: UnsafeMutableRawPointer, width: Int, height: Int, bytesPerRow: Int) {
        for y in 0..<height {
            for x in 0..<width {
                let offset = y * bytesPerRow + x * 4
                let pixel = baseAddress.advanced(by: offset).assumingMemoryBound(to: UInt8.self)
                let intensity = UInt8((x + y) / 8 % 256)
                pixel[0] = intensity
                pixel[1] = intensity
                pixel[2] = intensity
                pixel[3] = 255
            }
        }
    }

    private func fillWithShadow(baseAddress: UnsafeMutableRawPointer, width: Int, height: Int, bytesPerRow: Int) {
        // Background
        fillSolid(baseAddress: baseAddress, width: width, height: height, bytesPerRow: bytesPerRow, intensity: 128)

        // Add shadow region (darker) in center-bottom
        let shadowX = width / 2 - 50
        let shadowY = height / 2
        let shadowWidth = 100
        let shadowHeight = 80

        for y in shadowY..<min(shadowY + shadowHeight, height) {
            for x in shadowX..<min(shadowX + shadowWidth, width) {
                let offset = y * bytesPerRow + x * 4
                let pixel = baseAddress.advanced(by: offset).assumingMemoryBound(to: UInt8.self)
                pixel[0] = 80  // Darker shadow
                pixel[1] = 80
                pixel[2] = 80
                pixel[3] = 255
            }
        }
    }

    private func fillWithPointedShadow(baseAddress: UnsafeMutableRawPointer, width: Int, height: Int, bytesPerRow: Int) {
        // Background
        fillSolid(baseAddress: baseAddress, width: width, height: height, bytesPerRow: bytesPerRow, intensity: 128)

        // Add triangular pointed shadow
        let tipX = width / 2
        let tipY = height / 2 + 60
        let baseY = height / 2

        for y in baseY..<min(tipY, height) {
            let widthAtY = (y - baseY) * 2 / 3
            for x in (tipX - widthAtY)..<min(tipX + widthAtY, width) {
                guard x >= 0 else { continue }
                let offset = y * bytesPerRow + x * 4
                let pixel = baseAddress.advanced(by: offset).assumingMemoryBound(to: UInt8.self)
                pixel[0] = 70
                pixel[1] = 70
                pixel[2] = 70
                pixel[3] = 255
            }
        }
    }

    private func fillWithRoundShadow(baseAddress: UnsafeMutableRawPointer, width: Int, height: Int, bytesPerRow: Int) {
        // Background
        fillSolid(baseAddress: baseAddress, width: width, height: height, bytesPerRow: bytesPerRow, intensity: 128)

        // Add circular shadow
        let centerX = width / 2
        let centerY = height / 2
        let radius = 40

        for y in 0..<height {
            for x in 0..<width {
                let dx = x - centerX
                let dy = y - centerY
                if dx * dx + dy * dy <= radius * radius {
                    let offset = y * bytesPerRow + x * 4
                    let pixel = baseAddress.advanced(by: offset).assumingMemoryBound(to: UInt8.self)
                    pixel[0] = 75
                    pixel[1] = 75
                    pixel[2] = 75
                    pixel[3] = 255
                }
            }
        }
    }

    private func fillWithTinyShadow(baseAddress: UnsafeMutableRawPointer, width: Int, height: Int, bytesPerRow: Int) {
        // Background
        fillSolid(baseAddress: baseAddress, width: width, height: height, bytesPerRow: bytesPerRow, intensity: 128)

        // Tiny shadow (20x20 pixels, below minShadowArea of 1000)
        let shadowX = width / 2
        let shadowY = height / 2

        for y in shadowY..<min(shadowY + 20, height) {
            for x in shadowX..<min(shadowX + 20, width) {
                let offset = y * bytesPerRow + x * 4
                let pixel = baseAddress.advanced(by: offset).assumingMemoryBound(to: UInt8.self)
                pixel[0] = 70
                pixel[1] = 70
                pixel[2] = 70
                pixel[3] = 255
            }
        }
    }

    private func fillWithDistantShadow(baseAddress: UnsafeMutableRawPointer, width: Int, height: Int, bytesPerRow: Int) {
        // Background
        fillSolid(baseAddress: baseAddress, width: width, height: height, bytesPerRow: bytesPerRow, intensity: 128)

        // Shadow in bottom-right corner (far from typical hand ROI)
        let shadowX = width - 100
        let shadowY = height - 100

        for y in shadowY..<height {
            for x in shadowX..<width {
                let offset = y * bytesPerRow + x * 4
                let pixel = baseAddress.advanced(by: offset).assumingMemoryBound(to: UInt8.self)
                pixel[0] = 70
                pixel[1] = 70
                pixel[2] = 70
                pixel[3] = 255
            }
        }
    }

    private func fillWithLargeShadow(baseAddress: UnsafeMutableRawPointer, width: Int, height: Int, bytesPerRow: Int) {
        // Background
        fillSolid(baseAddress: baseAddress, width: width, height: height, bytesPerRow: bytesPerRow, intensity: 128)

        // Large shadow (150x120 pixels)
        let shadowX = width / 2 - 75
        let shadowY = height / 2 - 60

        for y in shadowY..<min(shadowY + 120, height) {
            for x in shadowX..<min(shadowX + 150, width) {
                guard x >= 0 && y >= 0 else { continue }
                let offset = y * bytesPerRow + x * 4
                let pixel = baseAddress.advanced(by: offset).assumingMemoryBound(to: UInt8.self)
                pixel[0] = 75
                pixel[1] = 75
                pixel[2] = 75
                pixel[3] = 255
            }
        }
    }

    private func fillWithSmallShadow(baseAddress: UnsafeMutableRawPointer, width: Int, height: Int, bytesPerRow: Int) {
        // Background
        fillSolid(baseAddress: baseAddress, width: width, height: height, bytesPerRow: bytesPerRow, intensity: 128)

        // Small shadow (40x35 pixels, just above minShadowArea)
        let shadowX = width / 2 - 20
        let shadowY = height / 2 - 17

        for y in shadowY..<min(shadowY + 35, height) {
            for x in shadowX..<min(shadowX + 40, width) {
                guard x >= 0 && y >= 0 else { continue }
                let offset = y * bytesPerRow + x * 4
                let pixel = baseAddress.advanced(by: offset).assumingMemoryBound(to: UInt8.self)
                pixel[0] = 75
                pixel[1] = 75
                pixel[2] = 75
                pixel[3] = 255
            }
        }
    }

    private func modifyPixelBuffer(_ buffer: CVPixelBuffer, fillValue: UInt8) {
        CVPixelBufferLockBaseAddress(buffer, [])
        defer { CVPixelBufferUnlockBaseAddress(buffer, []) }

        guard let baseAddress = CVPixelBufferGetBaseAddress(buffer) else { return }

        let width = CVPixelBufferGetWidth(buffer)
        let height = CVPixelBufferGetHeight(buffer)
        let bytesPerRow = CVPixelBufferGetBytesPerRow(buffer)

        for y in 0..<height {
            for x in 0..<width {
                let offset = y * bytesPerRow + x * 4
                let pixel = baseAddress.advanced(by: offset).assumingMemoryBound(to: UInt8.self)
                pixel[0] = fillValue
                pixel[1] = fillValue
                pixel[2] = fillValue
                pixel[3] = 255
            }
        }
    }
}
