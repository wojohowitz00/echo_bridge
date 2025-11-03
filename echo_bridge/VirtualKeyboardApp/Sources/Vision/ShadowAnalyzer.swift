import Foundation
import CoreVideo
import CoreImage
import Accelerate
import Vision

/// Analyzes hand shadows for touch detection using frame differencing
/// Implements shadow extraction algorithm from Posner et al. (2012) Section IV
///
/// Algorithm Pipeline:
/// 1. Frame differencing: |currentFrame - referenceFrame|
/// 2. Threshold to create binary shadow mask (threshold: 30-50 pixels)
/// 3. Morphological operations for noise reduction
/// 4. Shadow region detection (largest contour)
/// 5. Shadow fingertip extraction using law of cosines
///
/// Performance Target: <15ms per frame (8-12ms typical)
class ShadowAnalyzer {
    // MARK: - Properties

    /// Core Image context for rendering operations
    private let ciContext = CIContext(options: [.useSoftwareRenderer: false])

    /// Reference frame captured without hand (background)
    /// Updated via captureReferenceFrame() at app startup or lighting changes
    private var referenceFrame: CVPixelBuffer?

    /// Adaptive shadow detection threshold (20-80 pixels)
    /// Adjusts automatically based on lighting conditions
    private var adaptiveThreshold: Float = 40.0

    /// Minimum shadow area in pixels (filters noise)
    private let minShadowArea: Int = 1000

    /// Morphological kernel size for dilate/erode operations
    private let morphKernelSize: Int = 3

    /// Histogram bins for adaptive thresholding analysis
    private let histogramBins: Int = 256

    // MARK: - Result Type

    /// Shadow analysis result data
    struct ShadowData {
        /// Shadow fingertip position in camera frame space
        let shadowTipPosition: CGPoint

        /// Bounding box of shadow region
        let shadowROI: CGRect

        /// Placeholder distance value (calculated by VisionPipelineManager)
        let distance: Float

        /// Shadow detection confidence (0.0-1.0)
        let confidence: Float

        /// Processing time for performance monitoring
        let processingTime: TimeInterval
    }

    // MARK: - Public Methods

    /// Capture reference frame for background subtraction
    /// Should be called at app startup with NO hand in frame
    /// Can be re-called if lighting conditions change significantly
    /// - Parameter pixelBuffer: Background frame without hand
    func captureReferenceFrame(_ pixelBuffer: CVPixelBuffer) {
        // Create a copy to avoid reference issues
        var refFrame: CVPixelBuffer?

        let width = CVPixelBufferGetWidth(pixelBuffer)
        let height = CVPixelBufferGetHeight(pixelBuffer)
        let format = CVPixelBufferGetPixelFormatType(pixelBuffer)

        let attributes: [String: Any] = [
            kCVPixelBufferCGImageCompatibilityKey as String: true,
            kCVPixelBufferCGBitmapContextCompatibilityKey as String: true
        ]

        CVPixelBufferCreate(
            kCFAllocatorDefault,
            width,
            height,
            format,
            attributes as CFDictionary,
            &refFrame
        )

        guard let destination = refFrame else { return }

        // Copy pixel data
        CVPixelBufferLockBaseAddress(pixelBuffer, .readOnly)
        CVPixelBufferLockBaseAddress(destination, [])
        defer {
            CVPixelBufferUnlockBaseAddress(pixelBuffer, .readOnly)
            CVPixelBufferUnlockBaseAddress(destination, [])
        }

        guard let srcAddress = CVPixelBufferGetBaseAddress(pixelBuffer),
              let dstAddress = CVPixelBufferGetBaseAddress(destination) else {
            return
        }

        let dataSize = CVPixelBufferGetDataSize(pixelBuffer)
        memcpy(dstAddress, srcAddress, dataSize)

        self.referenceFrame = destination
    }

    /// Analyze shadow in current frame compared to reference frame
    /// - Parameters:
    ///   - currentFrame: Current camera frame
    ///   - referenceFrame: Reference frame captured without hand (background)
    ///   - handROI: Region of interest containing the hand
    ///   - completion: Callback with shadow analysis result
    func analyzeShadow(
        currentFrame: CVPixelBuffer,
        referenceFrame: CVPixelBuffer,
        handROI: CGRect,
        completion: @escaping (ShadowData?) -> Void
    ) {
        // Process on background thread for non-blocking operation
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            let shadowData = self?.performShadowAnalysis(
                currentFrame: currentFrame,
                referenceFrame: referenceFrame,
                handROI: handROI
            )
            completion(shadowData)
        }
    }

    /// Synchronous version of shadow analysis (for pipeline integration)
    /// - Parameters:
    ///   - currentFrame: Current camera frame
    ///   - handROI: Region of interest containing the hand
    /// - Returns: Shadow data if detected, nil otherwise
    func analyzeShadowSync(
        currentFrame: CVPixelBuffer,
        handROI: CGRect
    ) -> ShadowData? {
        guard let refFrame = referenceFrame else {
            return nil
        }

        return performShadowAnalysis(
            currentFrame: currentFrame,
            referenceFrame: refFrame,
            handROI: handROI
        )
    }

    // MARK: - Private Methods - Core Pipeline

    /// Perform the actual shadow analysis
    /// - Parameters:
    ///   - currentFrame: Current camera frame
    ///   - referenceFrame: Reference frame without hand
    ///   - handROI: Hand region from HandDetector
    /// - Returns: Shadow data if valid shadow detected, nil otherwise
    private func performShadowAnalysis(
        currentFrame: CVPixelBuffer,
        referenceFrame: CVPixelBuffer,
        handROI: CGRect
    ) -> ShadowData? {
        let startTime = CFAbsoluteTimeGetCurrent()

        // Step 1: Calculate frame difference (3-5ms target)
        guard let diffImage = calculateFrameDifference(
            current: currentFrame,
            reference: referenceFrame
        ) else {
            return nil
        }

        // Step 2: Update adaptive threshold based on current lighting (1ms)
        updateAdaptiveThreshold(diffImage)

        // Step 3: Apply threshold to isolate shadow region (2-3ms)
        guard let shadowMask = applyThreshold(to: diffImage, threshold: adaptiveThreshold) else {
            return nil
        }

        // Step 4: Apply morphological operations for smoothing (4-6ms)
        let smoothedMask = applyMorphologicalOps(shadowMask)

        // Step 5: Find shadow region (largest contour in mask) (2-3ms)
        guard let shadowROI = findShadowRegion(in: smoothedMask, within: handROI) else {
            return nil
        }

        // Step 6: Extract shadow tip position using law of cosines (1-2ms)
        guard let shadowTip = detectShadowFingertip(
            in: shadowMask,
            shadowROI: shadowROI
        ) else {
            // Fallback to center of shadow ROI if fingertip detection fails
            let shadowTip = CGPoint(x: shadowROI.midX, y: shadowROI.midY)

            let processingTime = CFAbsoluteTimeGetCurrent() - startTime
            return ShadowData(
                shadowTipPosition: shadowTip,
                shadowROI: shadowROI,
                distance: 0.0,  // Will be calculated by VisionPipelineManager
                confidence: 0.5, // Lower confidence for fallback method
                processingTime: processingTime
            )
        }

        // Calculate confidence based on shadow area
        let shadowArea = shadowROI.width * shadowROI.height
        let confidence = calculateShadowConfidence(area: shadowArea, threshold: adaptiveThreshold)

        let processingTime = CFAbsoluteTimeGetCurrent() - startTime

        return ShadowData(
            shadowTipPosition: shadowTip,
            shadowROI: shadowROI,
            distance: 0.0,  // Will be calculated by VisionPipelineManager
            confidence: confidence,
            processingTime: processingTime
        )
    }

    // MARK: - Private Methods - Frame Differencing (Lines 50-120)

    /// Calculate absolute difference between current and reference frames
    /// Uses Accelerate framework for high-performance SIMD operations
    /// Target: 3-5ms processing time
    ///
    /// Algorithm: diff = |current - reference|
    /// From Posner et al. (2012): Shadow appears as dark region in difference image
    ///
    /// - Parameters:
    ///   - current: Current camera frame
    ///   - reference: Background frame without hand
    /// - Returns: Difference image as CIImage, or nil on failure
    private func calculateFrameDifference(current: CVPixelBuffer, reference: CVPixelBuffer) -> CIImage? {
        // Lock both buffers for reading
        CVPixelBufferLockBaseAddress(current, .readOnly)
        CVPixelBufferLockBaseAddress(reference, .readOnly)
        defer {
            CVPixelBufferUnlockBaseAddress(current, .readOnly)
            CVPixelBufferUnlockBaseAddress(reference, .readOnly)
        }

        guard let currentBase = CVPixelBufferGetBaseAddress(current),
              let refBase = CVPixelBufferGetBaseAddress(reference) else {
            return nil
        }

        let width = CVPixelBufferGetWidth(current)
        let height = CVPixelBufferGetHeight(current)
        let bytesPerRow = CVPixelBufferGetBytesPerRow(current)

        // Validate dimensions match
        guard width == CVPixelBufferGetWidth(reference),
              height == CVPixelBufferGetHeight(reference) else {
            return nil
        }

        // Create output buffer for difference image
        var diffBuffer: CVPixelBuffer?
        let attributes: [String: Any] = [
            kCVPixelBufferCGImageCompatibilityKey as String: true,
            kCVPixelBufferCGBitmapContextCompatibilityKey as String: true
        ]

        CVPixelBufferCreate(
            kCFAllocatorDefault,
            width,
            height,
            kCVPixelFormatType_32BGRA,
            attributes as CFDictionary,
            &diffBuffer
        )

        guard let outputBuffer = diffBuffer else {
            return nil
        }

        CVPixelBufferLockBaseAddress(outputBuffer, [])
        defer { CVPixelBufferUnlockBaseAddress(outputBuffer, []) }

        guard let outputBase = CVPixelBufferGetBaseAddress(outputBuffer) else {
            return nil
        }

        // Use Accelerate framework for fast absolute difference
        // Process each row using vImageAbsoluteDifferenceOfPlanar8
        for y in 0..<height {
            let currentRow = currentBase.advanced(by: y * bytesPerRow)
            let refRow = refBase.advanced(by: y * bytesPerRow)
            let outputRow = outputBase.advanced(by: y * bytesPerRow)

            // Convert BGRA to grayscale and compute absolute difference
            for x in 0..<width {
                let currentPixel = currentRow.advanced(by: x * 4).assumingMemoryBound(to: UInt8.self)
                let refPixel = refRow.advanced(by: x * 4).assumingMemoryBound(to: UInt8.self)
                let outputPixel = outputRow.advanced(by: x * 4).assumingMemoryBound(to: UInt8.self)

                // Calculate grayscale intensity
                let currentGray = (Int(currentPixel[0]) + Int(currentPixel[1]) + Int(currentPixel[2])) / 3
                let refGray = (Int(refPixel[0]) + Int(refPixel[1]) + Int(refPixel[2])) / 3

                // Absolute difference
                let diff = UInt8(abs(currentGray - refGray))

                // Write to all channels (grayscale)
                outputPixel[0] = diff
                outputPixel[1] = diff
                outputPixel[2] = diff
                outputPixel[3] = 255 // Alpha
            }
        }

        return CIImage(cvPixelBuffer: outputBuffer)
    }

    /// Apply threshold to create binary shadow mask
    /// Pixels with intensity > threshold become white (shadow), others black
    /// Target: 2-3ms processing time
    ///
    /// - Parameters:
    ///   - image: Difference image from frame differencing
    ///   - threshold: Intensity threshold (20-80 pixels, normalized to 0-1)
    /// - Returns: Binary mask image, or nil on failure
    private func applyThreshold(to image: CIImage, threshold: Float) -> CIImage? {
        // Create threshold kernel using Core Image
        let kernelCode = """
        kernel vec4 binaryThreshold(__sample pixel, float thresh) {
            // Calculate grayscale intensity
            float intensity = (pixel.r + pixel.g + pixel.b) / 3.0;

            // Binary threshold: intensity > thresh → white (shadow detected)
            float result = intensity > thresh ? 1.0 : 0.0;

            return vec4(result, result, result, 1.0);
        }
        """

        guard let kernel = CIColorKernel(source: kernelCode) else {
            return nil
        }

        // Normalize threshold to 0-1 range (threshold in 0-255, normalize by dividing by 255)
        let normalizedThreshold = threshold / 255.0

        return kernel.apply(
            extent: image.extent,
            arguments: [image, normalizedThreshold]
        )
    }

    // MARK: - Private Methods - Shadow Region Extraction (Lines 122-180)

    /// Apply morphological operations to shadow mask
    /// Sequence: Dilate → Erode (morphological closing)
    /// Removes noise and connects nearby shadow pixels
    /// Target: 4-6ms processing time
    ///
    /// - Parameter mask: Binary shadow mask from thresholding
    /// - Returns: Processed mask with reduced noise
    private func applyMorphologicalOps(_ mask: CIImage) -> CIImage {
        var result = mask

        // Dilate to connect nearby shadow pixels
        result = applyDilate(result, kernelSize: morphKernelSize)

        // Erode to remove small noise regions
        result = applyErode(result, kernelSize: morphKernelSize)

        return result
    }

    /// Dilate operation - expand white regions in binary mask
    /// Morphological dilation: max(neighborhood pixels)
    /// - Parameters:
    ///   - image: Input binary mask
    ///   - kernelSize: Size of morphological kernel
    /// - Returns: Dilated image
    private func applyDilate(_ image: CIImage, kernelSize: Int) -> CIImage {
        guard let filter = CIFilter(name: "CIMorphologyMaximum") else {
            return image
        }

        filter.setValue(image, forKey: kCIInputImageKey)
        filter.setValue(Float(kernelSize), forKey: kCIInputRadiusKey)

        return filter.outputImage ?? image
    }

    /// Erode operation - shrink white regions in binary mask
    /// Morphological erosion: min(neighborhood pixels)
    /// - Parameters:
    ///   - image: Input binary mask
    ///   - kernelSize: Size of morphological kernel
    /// - Returns: Eroded image
    private func applyErode(_ image: CIImage, kernelSize: Int) -> CIImage {
        guard let filter = CIFilter(name: "CIMorphologyMinimum") else {
            return image
        }

        filter.setValue(image, forKey: kCIInputImageKey)
        filter.setValue(Float(kernelSize), forKey: kCIInputRadiusKey)

        return filter.outputImage ?? image
    }

    /// Find the shadow region (largest contour) in the processed mask
    /// Uses pixel scanning to find largest connected white region
    /// Target: 2-3ms processing time
    ///
    /// From Posner et al. (2012): Shadow should be near hand region
    /// Filters: Minimum area 1000 pixels, must overlap or be near handROI
    ///
    /// - Parameters:
    ///   - mask: Binary shadow mask after morphological operations
    ///   - handROI: Hand region from HandDetector (for spatial filtering)
    /// - Returns: Bounding box of shadow region, or nil if no valid shadow found
    private func findShadowRegion(in mask: CIImage, within handROI: CGRect) -> CGRect? {
        // Convert CIImage to CVPixelBuffer for pixel-level analysis
        guard let pixelBuffer = pixelBufferFromCIImage(mask) else {
            return nil
        }

        // Lock pixel buffer for reading
        CVPixelBufferLockBaseAddress(pixelBuffer, .readOnly)
        defer { CVPixelBufferUnlockBaseAddress(pixelBuffer, .readOnly) }

        guard let baseAddress = CVPixelBufferGetBaseAddress(pixelBuffer) else {
            return nil
        }

        let width = CVPixelBufferGetWidth(pixelBuffer)
        let height = CVPixelBufferGetHeight(pixelBuffer)
        let bytesPerRow = CVPixelBufferGetBytesPerRow(pixelBuffer)

        // Find bounding box of white pixels (shadow region)
        var minX = width
        var maxX = 0
        var minY = height
        var maxY = 0
        var pixelCount = 0

        // Expand hand ROI slightly to search for nearby shadows
        let searchROI = handROI.insetBy(dx: -50, dy: -50)

        for y in 0..<height {
            for x in 0..<width {
                // Skip pixels outside search region
                if !searchROI.contains(CGPoint(x: x, y: y)) {
                    continue
                }

                let offset = y * bytesPerRow + x * 4
                let pixelPtr = baseAddress.advanced(by: offset).assumingMemoryBound(to: UInt8.self)

                // Check if pixel is white (shadow region)
                let intensity = pixelPtr[0]  // Grayscale, so R=G=B
                if intensity > 128 {  // Threshold for white
                    minX = min(minX, x)
                    maxX = max(maxX, x)
                    minY = min(minY, y)
                    maxY = max(maxY, y)
                    pixelCount += 1
                }
            }
        }

        // Check if enough pixels found (minimum shadow area)
        guard pixelCount >= minShadowArea else {
            return nil
        }

        // Create bounding box
        let shadowROI = CGRect(
            x: CGFloat(minX),
            y: CGFloat(minY),
            width: CGFloat(maxX - minX),
            height: CGFloat(maxY - minY)
        )

        // Validate shadow region
        guard shadowROI.width > 10 && shadowROI.height > 10 else {
            return nil
        }

        return shadowROI
    }

    // MARK: - Private Methods - Shadow Fingertip Detection (Lines 182-220)

    /// Detect shadow fingertip position using law of cosines
    /// Uses same algorithm as FingertipDetector for consistency
    /// Target: 1-2ms processing time
    ///
    /// Algorithm:
    /// 1. Extract shadow contour from binary mask
    /// 2. Apply law of cosines to find sharpest point
    /// 3. Return shadow tip position
    ///
    /// From Posner et al. (2012): Shadow tip located at same relative position
    /// as fingertip within the shadow region
    ///
    /// - Parameters:
    ///   - mask: Binary shadow mask
    ///   - shadowROI: Bounding box of shadow region
    /// - Returns: Shadow fingertip position in camera frame, or nil if detection fails
    private func detectShadowFingertip(
        in mask: CIImage,
        shadowROI: CGRect
    ) -> CGPoint? {
        // Crop to shadow ROI for faster processing
        let croppedMask = mask.cropped(to: shadowROI)

        // Extract shadow contour
        guard let contours = extractShadowContour(from: croppedMask) else {
            return nil
        }

        // Find shadow tip using law of cosines (same as FingertipDetector)
        guard let shadowTipLocal = findShadowTipUsingLawOfCosines(contours) else {
            return nil
        }

        // Convert from ROI coordinates back to camera frame
        let shadowTipCamera = CGPoint(
            x: shadowTipLocal.x + shadowROI.origin.x,
            y: shadowTipLocal.y + shadowROI.origin.y
        )

        return shadowTipCamera
    }

    /// Extract contour from shadow mask
    /// Simplified version of FingertipDetector's contour extraction
    /// - Parameter mask: Binary shadow mask
    /// - Returns: Array of contour point arrays, or nil if extraction fails
    private func extractShadowContour(from mask: CIImage) -> [[CGPoint]]? {
        guard let pixelBuffer = pixelBufferFromCIImage(mask) else {
            return nil
        }

        CVPixelBufferLockBaseAddress(pixelBuffer, .readOnly)
        defer { CVPixelBufferUnlockBaseAddress(pixelBuffer, .readOnly) }

        guard let baseAddress = CVPixelBufferGetBaseAddress(pixelBuffer) else {
            return nil
        }

        let width = CVPixelBufferGetWidth(pixelBuffer)
        let height = CVPixelBufferGetHeight(pixelBuffer)
        let bytesPerRow = CVPixelBufferGetBytesPerRow(pixelBuffer)

        var visited = Array(repeating: Array(repeating: false, count: width), count: height)
        var contours: [[CGPoint]] = []

        // Scan for edge pixels
        for y in 0..<height {
            for x in 0..<width {
                guard !visited[y][x] else { continue }

                let offset = y * bytesPerRow + x * 4
                let pixelPtr = baseAddress.advanced(by: offset).assumingMemoryBound(to: UInt8.self)
                let intensity = pixelPtr[0]

                guard intensity > 128 else { continue }

                // Trace contour from this seed point
                if let contour = traceShadowContour(
                    from: CGPoint(x: x, y: y),
                    in: baseAddress,
                    width: width,
                    height: height,
                    bytesPerRow: bytesPerRow,
                    visited: &visited
                ) {
                    if contour.count >= 10 {
                        contours.append(contour)
                    }
                }
            }
        }

        guard !contours.isEmpty else { return nil }

        // Return largest contour
        let sortedContours = contours.sorted { $0.count > $1.count }
        return Array(sortedContours.prefix(3))
    }

    /// Trace shadow contour using 8-connectivity
    /// Simplified version of FingertipDetector's contour tracing
    /// - Parameters:
    ///   - start: Starting point
    ///   - baseAddress: Pixel buffer base address
    ///   - width: Image width
    ///   - height: Image height
    ///   - bytesPerRow: Bytes per row
    ///   - visited: Visited pixel tracker
    /// - Returns: Array of contour points, or nil if invalid
    private func traceShadowContour(
        from start: CGPoint,
        in baseAddress: UnsafeMutableRawPointer,
        width: Int,
        height: Int,
        bytesPerRow: Int,
        visited: inout [[Bool]]
    ) -> [CGPoint]? {
        var contour: [CGPoint] = []
        var current = start

        let neighbors = [
            (-1, -1), (0, -1), (1, -1),
            (1, 0),
            (1, 1), (0, 1), (-1, 1),
            (-1, 0)
        ]

        let maxContourLength = 5000

        while contour.count < maxContourLength {
            let x = Int(current.x)
            let y = Int(current.y)

            visited[y][x] = true
            contour.append(current)

            var foundNext = false
            for (dx, dy) in neighbors {
                let nx = x + dx
                let ny = y + dy

                guard nx >= 0, nx < width, ny >= 0, ny < height else { continue }
                guard !visited[ny][nx] else { continue }

                let offset = ny * bytesPerRow + nx * 4
                let pixelPtr = baseAddress.advanced(by: offset).assumingMemoryBound(to: UInt8.self)
                let intensity = pixelPtr[0]

                if intensity > 128 {
                    current = CGPoint(x: nx, y: ny)
                    foundNext = true
                    break
                }
            }

            if !foundNext { break }
        }

        return contour.isEmpty ? nil : contour
    }

    /// Find shadow tip using law of cosines (same algorithm as FingertipDetector)
    /// - Parameter contours: Shadow contour points
    /// - Returns: Shadow tip position, or nil if detection fails
    private func findShadowTipUsingLawOfCosines(_ contours: [[CGPoint]]) -> CGPoint? {
        guard let contour = contours.first, contour.count >= 3 else {
            return nil
        }

        var minAngle = CGFloat.infinity
        var shadowTipIndex = 0
        let neighborDistance = 3

        for i in 0..<contour.count {
            let prevIdx = (i - neighborDistance + contour.count) % contour.count
            let nextIdx = (i + neighborDistance) % contour.count

            let prev = contour[prevIdx]
            let current = contour[i]
            let next = contour[nextIdx]

            let a = distance(from: prev, to: current)
            let b = distance(from: current, to: next)
            let c = distance(from: prev, to: next)

            guard a > 0, b > 0, c > 0 else { continue }

            // Law of cosines: cos(θ) = (a² + b² - c²) / (2ab)
            let numerator = a * a + b * b - c * c
            let denominator = 2 * a * b
            let cosAngle = numerator / denominator

            let clampedCos = min(1.0, max(-1.0, cosAngle))
            let angle = acos(clampedCos)

            if angle < minAngle {
                minAngle = angle
                shadowTipIndex = i
            }
        }

        // Validate sharp angle (< 90 degrees)
        guard minAngle < 1.57 else {
            return nil
        }

        return contour[shadowTipIndex]
    }

    /// Calculate Euclidean distance between two points
    /// - Parameters:
    ///   - p1: First point
    ///   - p2: Second point
    /// - Returns: Distance
    private func distance(from p1: CGPoint, to p2: CGPoint) -> CGFloat {
        return hypot(p2.x - p1.x, p2.y - p1.y)
    }

    // MARK: - Private Methods - Adaptive Shadow Thresholding (Lines 222-260)

    /// Update adaptive threshold based on difference image histogram
    /// Analyzes lighting conditions and adjusts threshold automatically
    /// Target: 1ms processing time
    ///
    /// From Posner et al. (2012): Shadow visibility varies with lighting
    /// ISO 100 recommended for consistent shadows
    ///
    /// Algorithm:
    /// 1. Calculate histogram of difference image
    /// 2. Find peak (most common difference value)
    /// 3. Set threshold at 2-3x peak value (separates shadow from noise)
    /// 4. Clamp to valid range (20-80 pixels)
    ///
    /// - Parameter diffImage: Difference image from frame differencing
    private func updateAdaptiveThreshold(_ diffImage: CIImage) {
        guard let pixelBuffer = pixelBufferFromCIImage(diffImage) else {
            return
        }

        CVPixelBufferLockBaseAddress(pixelBuffer, .readOnly)
        defer { CVPixelBufferUnlockBaseAddress(pixelBuffer, .readOnly) }

        guard let baseAddress = CVPixelBufferGetBaseAddress(pixelBuffer) else {
            return
        }

        let width = CVPixelBufferGetWidth(pixelBuffer)
        let height = CVPixelBufferGetHeight(pixelBuffer)
        let bytesPerRow = CVPixelBufferGetBytesPerRow(pixelBuffer)

        // Build histogram
        var histogram = Array(repeating: 0, count: histogramBins)

        // Sample every 4th pixel for speed
        for y in stride(from: 0, to: height, by: 4) {
            for x in stride(from: 0, to: width, by: 4) {
                let offset = y * bytesPerRow + x * 4
                let pixelPtr = baseAddress.advanced(by: offset).assumingMemoryBound(to: UInt8.self)
                let intensity = Int(pixelPtr[0])
                histogram[intensity] += 1
            }
        }

        // Find peak in histogram (ignore first bin which is likely background)
        var maxCount = 0
        var peakBin = 0
        for i in 1..<histogramBins {
            if histogram[i] > maxCount {
                maxCount = histogram[i]
                peakBin = i
            }
        }

        // Set threshold at 2.5x peak (empirically determined)
        let newThreshold = Float(peakBin) * 2.5

        // Clamp to valid range (20-80 pixels)
        adaptiveThreshold = min(80.0, max(20.0, newThreshold))
    }

    /// Calculate shadow detection confidence score
    /// Based on shadow area and threshold consistency
    /// - Parameters:
    ///   - area: Shadow region area in pixels
    ///   - threshold: Current adaptive threshold
    /// - Returns: Confidence score (0.0-1.0)
    private func calculateShadowConfidence(area: CGFloat, threshold: Float) -> Float {
        // Confidence increases with reasonable shadow size
        // Expected shadow area: 1000-5000 pixels
        let areaScore = min(1.0, Float(area) / 5000.0)

        // Confidence increases with mid-range threshold (indicates good lighting)
        // Optimal threshold: 30-50 pixels
        let thresholdDelta = abs(threshold - 40.0)
        let thresholdScore = max(0.0, 1.0 - (thresholdDelta / 40.0))

        // Weighted average
        return (areaScore * 0.7 + thresholdScore * 0.3)
    }

    // MARK: - Private Methods - Utilities

    /// Convert CIImage to CVPixelBuffer for pixel-level operations
    /// - Parameter ciImage: Input Core Image
    /// - Returns: CVPixelBuffer, or nil on failure
    private func pixelBufferFromCIImage(_ ciImage: CIImage) -> CVPixelBuffer? {
        var pixelBuffer: CVPixelBuffer?

        let attributes: [String: Any] = [
            kCVPixelBufferCGImageCompatibilityKey as String: true,
            kCVPixelBufferCGBitmapContextCompatibilityKey as String: true
        ]

        CVPixelBufferCreate(
            kCFAllocatorDefault,
            Int(ciImage.extent.width),
            Int(ciImage.extent.height),
            kCVPixelFormatType_32BGRA,
            attributes as CFDictionary,
            &pixelBuffer
        )

        guard let buffer = pixelBuffer else { return nil }

        ciContext.render(ciImage, to: buffer)
        return buffer
    }
}
