import Foundation
import CoreGraphics
import CoreImage
import Vision

/// Detects fingertip position using contour analysis
/// Implements algorithm from Borade et al. (2016) using law of cosines
class FingertipDetector {
    // MARK: - Methods

    /// Detect fingertip position in a hand ROI
    /// - Parameters:
    ///   - pixelBuffer: Camera frame as CVPixelBuffer
    ///   - handROI: Region of interest containing the hand
    /// - Returns: Fingertip coordinates in camera frame space
    func detectFingertip(in pixelBuffer: CVPixelBuffer, within handROI: CGRect) -> CGPoint? {
        // Extract the hand region
        let ciImage = CIImage(cvPixelBuffer: pixelBuffer)
        let croppedImage = ciImage.cropped(to: handROI)

        // Apply Canny edge detection
        guard let edges = applyCanny(to: croppedImage) else {
            return nil
        }

        // Extract contours
        guard let contours = extractContours(from: edges) else {
            return nil
        }

        // Find fingertip using law of cosines
        guard let fingertip = findFingertipUsingLawOfCosines(contours) else {
            return nil
        }

        // Convert from ROI coordinates back to camera frame
        let cameraFramePoint = CGPoint(
            x: fingertip.x + handROI.origin.x,
            y: fingertip.y + handROI.origin.y
        )

        return cameraFramePoint
    }

    // MARK: - Private Methods

    /// Apply Canny edge detection to find hand boundaries
    /// Implements two-stage edge detection: Gaussian blur + edge extraction
    /// Parameters from Borade et al. (2016): Low threshold 50, High threshold 150, Kernel 3x3
    /// - Parameter image: Hand ROI as CIImage
    /// - Returns: Binary edge map with single-pixel edges, or nil on failure
    private func applyCanny(to image: CIImage) -> CIImage? {
        // Step 1: Gaussian blur for noise reduction (kernel size ~3x3, sigma ~1.4)
        // This smoothing is critical before edge detection
        let blurFilter = CIFilter(name: "CIGaussianBlur")
        blurFilter?.setValue(image, forKey: kCIInputImageKey)
        blurFilter?.setValue(NSNumber(value: 1.4), forKey: kCIInputRadiusKey)

        guard let blurred = blurFilter?.outputImage else {
            return nil
        }

        // Step 2: Apply Sobel-based edge detection (Core Image approximation of Canny)
        // CIEdges uses a Sobel operator which is similar to Canny's gradient calculation
        let edgeFilter = CIFilter(name: "CIEdges")
        edgeFilter?.setValue(blurred, forKey: kCIInputImageKey)
        edgeFilter?.setValue(NSNumber(value: 2.0), forKey: "inputIntensity")

        guard let edges = edgeFilter?.outputImage else {
            return nil
        }

        // Step 3: Threshold to binary (emulating Canny's hysteresis thresholding)
        // This converts gradient magnitudes to binary edges
        let thresholdKernel = """
        kernel vec4 binaryThreshold(__sample pixel, float low, float high) {
            float gray = (pixel.r + pixel.g + pixel.b) / 3.0;

            // Hysteresis thresholding approximation
            // Strong edges: above high threshold
            // Weak edges connected to strong: between low and high
            float result = gray > high ? 1.0 : (gray > low ? 0.5 : 0.0);

            return vec4(result, result, result, 1.0);
        }
        """

        guard let kernel = CIColorKernel(source: thresholdKernel) else {
            return edges
        }

        // Normalize to 0-1 range: low=50/255≈0.196, high=150/255≈0.588
        let binaryEdges = kernel.apply(
            extent: edges.extent,
            arguments: [edges, 0.196, 0.588]
        )

        return binaryEdges
    }

    /// Extract contours from edge-detected image using pixel scanning
    /// Implements boundary following algorithm to extract ordered contour points
    /// - Parameter edgeImage: Binary edge map from Canny detection
    /// - Returns: Array of contours, each as array of ordered CGPoints, or nil if no contours found
    private func extractContours(from edgeImage: CIImage) -> [[CGPoint]]? {
        // Convert CIImage to CVPixelBuffer for pixel-level access
        guard let pixelBuffer = pixelBufferFromCIImage(edgeImage) else {
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

        // Track visited pixels to avoid duplicates
        var visited = Array(repeating: Array(repeating: false, count: width), count: height)
        var contours: [[CGPoint]] = []

        // Scan for edge pixels and extract contours
        for y in 0..<height {
            for x in 0..<width {
                // Skip if already visited
                guard !visited[y][x] else { continue }

                // Check if this is an edge pixel
                let offset = y * bytesPerRow + x * 4
                let pixelPtr = baseAddress.advanced(by: offset).assumingMemoryBound(to: UInt8.self)
                let intensity = pixelPtr[0] // Grayscale, so R=G=B

                // Edge pixels are bright (> threshold)
                guard intensity > 128 else { continue }

                // Found an edge pixel - trace the contour
                if let contour = traceContour(
                    from: CGPoint(x: x, y: y),
                    in: baseAddress,
                    width: width,
                    height: height,
                    bytesPerRow: bytesPerRow,
                    visited: &visited
                ) {
                    // Only keep contours with sufficient points
                    if contour.count >= 10 {
                        contours.append(contour)
                    }
                }
            }
        }

        // Return largest contour (most likely the hand boundary)
        guard !contours.isEmpty else { return nil }

        // Sort by contour length and return top contours
        let sortedContours = contours.sorted { $0.count > $1.count }
        return Array(sortedContours.prefix(3)) // Return top 3 largest contours
    }

    /// Trace a single contour starting from a seed point using 8-connectivity
    /// - Parameters:
    ///   - start: Starting edge pixel coordinate
    ///   - baseAddress: Pixel buffer base address
    ///   - width: Image width
    ///   - height: Image height
    ///   - bytesPerRow: Bytes per row in pixel buffer
    ///   - visited: 2D array tracking visited pixels
    /// - Returns: Ordered array of contour points, or nil if invalid
    private func traceContour(
        from start: CGPoint,
        in baseAddress: UnsafeMutableRawPointer,
        width: Int,
        height: Int,
        bytesPerRow: Int,
        visited: inout [[Bool]]
    ) -> [CGPoint]? {
        var contour: [CGPoint] = []
        var current = start

        // 8-connectivity neighborhood offsets (clockwise from top)
        let neighbors = [
            (-1, -1), (0, -1), (1, -1),  // Top row
            (1, 0),                       // Right
            (1, 1), (0, 1), (-1, 1),     // Bottom row
            (-1, 0)                       // Left
        ]

        // Maximum contour length to prevent infinite loops
        let maxContourLength = 10000

        while contour.count < maxContourLength {
            let x = Int(current.x)
            let y = Int(current.y)

            // Mark as visited
            visited[y][x] = true
            contour.append(current)

            // Find next edge pixel in neighborhood
            var foundNext = false
            for (dx, dy) in neighbors {
                let nx = x + dx
                let ny = y + dy

                // Check bounds
                guard nx >= 0, nx < width, ny >= 0, ny < height else { continue }
                guard !visited[ny][nx] else { continue }

                // Check if neighbor is edge pixel
                let offset = ny * bytesPerRow + nx * 4
                let pixelPtr = baseAddress.advanced(by: offset).assumingMemoryBound(to: UInt8.self)
                let intensity = pixelPtr[0]

                if intensity > 128 {
                    current = CGPoint(x: nx, y: ny)
                    foundNext = true
                    break
                }
            }

            // No more connected edge pixels - contour complete
            if !foundNext {
                break
            }
        }

        return contour.isEmpty ? nil : contour
    }

    /// Convert CIImage to CVPixelBuffer for pixel-level operations
    /// - Parameter ciImage: Input Core Image
    /// - Returns: CVPixelBuffer, or nil on failure
    private func pixelBufferFromCIImage(_ ciImage: CIImage) -> CVPixelBuffer? {
        let ciContext = CIContext(options: [.useSoftwareRenderer: false])
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

    /// Find fingertip using law of cosines on contour points
    /// Implements algorithm from Borade et al. (2016): The fingertip has the sharpest angle (minimum angle)
    ///
    /// Algorithm:
    /// 1. For each contour point P_i:
    ///    - Form triangle with neighbors: P_{i-1}, P_i, P_{i+1}
    ///    - Calculate angle at P_i using law of cosines
    /// 2. Find point with minimum angle (sharpest corner)
    /// 3. Apply sub-pixel refinement for accuracy
    ///
    /// Law of Cosines: cos(θ) = (a² + b² - c²) / (2ab)
    /// where:
    ///   a = distance(P_{i-1}, P_i)
    ///   b = distance(P_i, P_{i+1})
    ///   c = distance(P_{i-1}, P_{i+1})
    ///
    /// - Parameter contours: Array of contour point arrays from edge detection
    /// - Returns: Fingertip coordinate with sub-pixel precision, or nil if no valid fingertip found
    private func findFingertipUsingLawOfCosines(_ contours: [[CGPoint]]) -> CGPoint? {
        // Use largest contour (most likely the hand boundary)
        guard let contour = contours.first, contour.count >= 3 else {
            return nil
        }

        var minAngle = CGFloat.infinity
        var fingertipIndex = 0

        // Window size for angle calculation (use neighbors at distance N)
        // Larger window = smoother but less precise, smaller = noisier but more precise
        let neighborDistance = 3

        // Iterate through contour points to find sharpest angle
        for i in 0..<contour.count {
            // Get neighboring points with wrap-around
            let prevIdx = (i - neighborDistance + contour.count) % contour.count
            let nextIdx = (i + neighborDistance) % contour.count

            let prev = contour[prevIdx]
            let current = contour[i]
            let next = contour[nextIdx]

            // Calculate triangle side lengths
            let a = distance(from: prev, to: current)  // Edge from previous to current
            let b = distance(from: current, to: next)  // Edge from current to next
            let c = distance(from: prev, to: next)     // Edge across (prev to next)

            // Prevent division by zero or invalid triangles
            guard a > 0, b > 0, c > 0 else { continue }

            // Apply law of cosines: cos(θ) = (a² + b² - c²) / (2ab)
            let numerator = a * a + b * b - c * c
            let denominator = 2 * a * b
            let cosAngle = numerator / denominator

            // Clamp to valid range [-1, 1] to avoid domain errors in acos
            let clampedCos = min(1.0, max(-1.0, cosAngle))
            let angle = acos(clampedCos)

            // Track minimum angle (sharpest point = fingertip)
            if angle < minAngle {
                minAngle = angle
                fingertipIndex = i
            }
        }

        // Validate that we found a sharp angle (not just noise)
        // Typical fingertip angle: 20-60 degrees (0.35-1.05 radians)
        // If angle is too large (>90°), likely not a fingertip
        guard minAngle < 1.57 else { // 1.57 radians ≈ 90 degrees
            return nil
        }

        // Get initial fingertip point
        let fingertip = contour[fingertipIndex]

        // Apply sub-pixel refinement for improved accuracy
        return refineFingetipSubPixel(
            fingertip,
            index: fingertipIndex,
            contour: contour
        )
    }

    /// Refine fingertip position to sub-pixel precision
    /// Uses weighted average of neighboring points based on their angles
    /// - Parameters:
    ///   - point: Initial fingertip point from law of cosines
    ///   - index: Index of fingertip in contour
    ///   - contour: Full contour array
    /// - Returns: Refined fingertip position with sub-pixel accuracy
    private func refineFingetipSubPixel(
        _ point: CGPoint,
        index: Int,
        contour: [CGPoint]
    ) -> CGPoint {
        // Window size for sub-pixel refinement
        let windowSize = 2

        var weightedX: CGFloat = 0
        var weightedY: CGFloat = 0
        var totalWeight: CGFloat = 0

        // Sample neighboring points and weight by distance to center
        for offset in -windowSize...windowSize {
            let idx = (index + offset + contour.count) % contour.count
            let neighbor = contour[idx]

            // Weight decreases with distance from center point
            // Use Gaussian-like weighting: exp(-distance²)
            let dist = distance(from: point, to: neighbor)
            let weight = exp(-dist * dist / 4.0)

            weightedX += neighbor.x * weight
            weightedY += neighbor.y * weight
            totalWeight += weight
        }

        // Return weighted average (sub-pixel refined position)
        guard totalWeight > 0 else { return point }

        return CGPoint(
            x: weightedX / totalWeight,
            y: weightedY / totalWeight
        )
    }

    /// Helper: Calculate Euclidean distance between two points
    private func distance(from p1: CGPoint, to p2: CGPoint) -> CGFloat {
        return hypot(p2.x - p1.x, p2.y - p1.y)
    }
}
