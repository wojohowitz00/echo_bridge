import Foundation
import CoreImage
import CoreVideo
import Accelerate

/// Detects hand regions in camera frames using HSV color segmentation
/// Implements hand detection algorithm from Posner et al. (2012) Section III and Borade et al. (2016)
///
/// Algorithm Pipeline:
/// 1. RGB → HSV color space conversion
/// 2. Skin tone detection using HSV range filters
/// 3. Morphological operations (dilate → erode → dilate) for noise reduction
/// 4. Contour detection to find largest hand region
/// 5. Bounding box extraction as hand ROI
class HandDetector {
    // MARK: - Properties

    /// Core Image context for rendering operations
    private let ciContext = CIContext(options: [.useSoftwareRenderer: false])

    // MARK: HSV Color Ranges for Skin Tone Detection
    // From Posner et al. (2012) Section III.1

    /// Hue range for skin detection (in degrees 0-360)
    /// Covers reddish skin tones: 0-20° and 335-360°
    private var hueRange1: (min: Float, max: Float) = (0, 20)
    private var hueRange2: (min: Float, max: Float) = (335, 360)

    /// Saturation range for skin (percentage 0-100)
    /// Typical skin saturation: 10-40%
    private var saturationRange: (min: Float, max: Float) = (10, 40)

    /// Value/Brightness range for skin (0-255)
    /// Accounts for various lighting conditions: 60-255
    private var valueRange: (min: Float, max: Float) = (60, 255)

    /// Morphological kernel size for dilate/erode operations
    private let morphKernelSize: Int = 5

    /// Minimum contour area to be considered a hand (in pixels)
    /// Filters out small noise regions
    private let minHandArea: Int = 5000

    /// Confidence threshold for hand detection (0.0-1.0)
    private let confidenceThreshold: Float = 0.7

    // MARK: - Public Methods

    /// Detect hand region in a pixel buffer using HSV-based color segmentation
    /// - Parameter pixelBuffer: Camera frame as CVPixelBuffer
    /// - Returns: HandData if hand detected with sufficient confidence, nil otherwise
    /// - Complexity: O(width × height) for pixel-level operations
    func detectHand(in pixelBuffer: CVPixelBuffer) -> HandData? {
        let startTime = CFAbsoluteTimeGetCurrent()

        // Convert to CIImage for Core Image processing
        let ciImage = CIImage(cvPixelBuffer: pixelBuffer)

        // Step 1: Convert RGB to HSV color space
        guard let hsvImage = convertToHSV(ciImage) else {
            return nil
        }

        // Step 2: Apply skin tone color range filter
        guard let skinMask = applyColorRangeFilter(hsvImage) else {
            return nil
        }

        // Step 3: Apply morphological operations for noise reduction
        let processedMask = applyMorphologicalOps(skinMask)

        // Step 4: Find largest hand contour in binary mask
        guard let handROI = findHandContour(processedMask, originalSize: ciImage.extent) else {
            return nil
        }

        // Calculate detection confidence based on ROI area
        let roiArea = handROI.width * handROI.height
        let frameArea = ciImage.extent.width * ciImage.extent.height
        let areaRatio = Float(roiArea / frameArea)

        // Confidence increases with reasonable hand size (5-30% of frame)
        let confidence = min(1.0, max(0.0, areaRatio * 10.0))

        // Only return hand data if confidence exceeds threshold
        guard confidence >= confidenceThreshold else {
            return nil
        }

        // Calculate processing time (available for performance monitoring)
        _ = CFAbsoluteTimeGetCurrent() - startTime

        // Fingertip position will be refined by FingertipDetector
        // For now, use center of ROI as initial estimate
        let fingertipPos = CGPoint(x: handROI.midX, y: handROI.midY)

        return HandData(
            fingertipPosition: fingertipPos,
            shadowTipPosition: CGPoint.zero,  // Updated by ShadowAnalyzer
            fingerShadowDistance: Float.greatestFiniteMagnitude,  // Updated by TouchValidator
            handROI: handROI,
            detectionConfidence: confidence,
            timestamp: Date(),
            frameNumber: 0  // Updated by VisionPipelineManager
        )
    }

    /// Calibrate HSV color ranges based on current lighting conditions
    /// Analyzes hand region in frame and adjusts color thresholds adaptively
    /// - Parameter pixelBuffer: Reference frame containing user's hand
    func calibrate(with pixelBuffer: CVPixelBuffer) {
        // Lock pixel buffer for reading
        CVPixelBufferLockBaseAddress(pixelBuffer, .readOnly)
        defer { CVPixelBufferUnlockBaseAddress(pixelBuffer, .readOnly) }

        guard let baseAddress = CVPixelBufferGetBaseAddress(pixelBuffer) else {
            return
        }

        let width = CVPixelBufferGetWidth(pixelBuffer)
        let height = CVPixelBufferGetHeight(pixelBuffer)
        let bytesPerRow = CVPixelBufferGetBytesPerRow(pixelBuffer)

        // Sample center region of frame (assume hand is positioned there)
        let sampleRegion = CGRect(
            x: width / 4,
            y: height / 4,
            width: width / 2,
            height: height / 2
        )

        var hueSum: Float = 0
        var satSum: Float = 0
        var valSum: Float = 0
        var sampleCount: Int = 0

        // Iterate through sample region
        for y in Int(sampleRegion.minY)..<Int(sampleRegion.maxY) {
            for x in Int(sampleRegion.minX)..<Int(sampleRegion.maxX) {
                let offset = y * bytesPerRow + x * 4
                let pixelPtr = baseAddress.advanced(by: offset).assumingMemoryBound(to: UInt8.self)

                // Extract BGRA components
                let b = Float(pixelPtr[0])
                let g = Float(pixelPtr[1])
                let r = Float(pixelPtr[2])

                // Convert RGB to HSV
                let hsv = rgbToHSV(r: r / 255.0, g: g / 255.0, b: b / 255.0)

                hueSum += hsv.h
                satSum += hsv.s
                valSum += hsv.v
                sampleCount += 1
            }
        }

        // Calculate average HSV values
        let avgHue = hueSum / Float(sampleCount)
        let avgSat = satSum / Float(sampleCount)
        let avgVal = valSum / Float(sampleCount)

        // Adjust ranges based on sampled values (±10° hue, ±15% saturation, ±30 value)
        let hueMargin: Float = 10
        let satMargin: Float = 15
        let valMargin: Float = 30

        // Update hue ranges (handling wrap-around at 0/360)
        if avgHue < 30 || avgHue > 330 {
            // Reddish tones - update range 1
            hueRange1 = (
                min: max(0, avgHue - hueMargin),
                max: min(20, avgHue + hueMargin)
            )
        }

        // Update saturation range
        saturationRange = (
            min: max(0, avgSat - satMargin),
            max: min(100, avgSat + satMargin)
        )

        // Update value range
        valueRange = (
            min: max(0, avgVal - valMargin),
            max: min(255, avgVal + valMargin)
        )
    }

    // MARK: - Private Methods - Color Space Conversion

    /// Convert RGB image to HSV color space using custom Core Image kernel
    /// HSV provides better color segmentation for skin tone detection
    /// - Parameter ciImage: Input RGB image
    /// - Returns: HSV image with H, S, V in separate channels, or nil on failure
    private func convertToHSV(_ ciImage: CIImage) -> CIImage? {
        // Create custom Core Image kernel for RGB → HSV conversion
        // HSV formula:
        // H (hue) = angle on color wheel (0-360°)
        // S (saturation) = color intensity (0-100%)
        // V (value) = brightness (0-255)

        let kernelCode = """
        kernel vec4 rgbToHSV(__sample pixel) {
            float r = pixel.r;
            float g = pixel.g;
            float b = pixel.b;
            float a = pixel.a;

            float maxC = max(r, max(g, b));
            float minC = min(r, min(g, b));
            float delta = maxC - minC;

            // Calculate Hue (0-360 degrees, normalized to 0-1)
            float h = 0.0;
            if (delta > 0.0) {
                if (maxC == r) {
                    h = mod((g - b) / delta, 6.0);
                } else if (maxC == g) {
                    h = ((b - r) / delta) + 2.0;
                } else {
                    h = ((r - g) / delta) + 4.0;
                }
                h = h / 6.0;  // Normalize to 0-1
            }

            // Calculate Saturation (0-1)
            float s = 0.0;
            if (maxC > 0.0) {
                s = delta / maxC;
            }

            // Value is just the max component (0-1)
            float v = maxC;

            return vec4(h, s, v, a);
        }
        """

        guard let kernel = CIColorKernel(source: kernelCode) else {
            return nil
        }

        return kernel.apply(extent: ciImage.extent, arguments: [ciImage])
    }

    /// Helper function: Convert single RGB pixel to HSV
    /// - Parameters:
    ///   - r: Red component (0-1)
    ///   - g: Green component (0-1)
    ///   - b: Blue component (0-1)
    /// - Returns: HSV tuple (h: 0-360, s: 0-100, v: 0-255)
    private func rgbToHSV(r: Float, g: Float, b: Float) -> (h: Float, s: Float, v: Float) {
        let maxC = max(r, g, b)
        let minC = min(r, g, b)
        let delta = maxC - minC

        var h: Float = 0
        if delta > 0 {
            if maxC == r {
                h = 60 * ((g - b) / delta).truncatingRemainder(dividingBy: 6)
            } else if maxC == g {
                h = 60 * (((b - r) / delta) + 2)
            } else {
                h = 60 * (((r - g) / delta) + 4)
            }
        }
        if h < 0 { h += 360 }

        let s = maxC == 0 ? 0 : (delta / maxC) * 100
        let v = maxC * 255

        return (h, s, v)
    }

    // MARK: - Private Methods - Color Filtering

    /// Apply HSV color range filter for skin tone detection
    /// Creates binary mask: white for skin pixels, black otherwise
    /// - Parameter hsvImage: Input image in HSV color space
    /// - Returns: Binary mask image, or nil on failure
    private func applyColorRangeFilter(_ hsvImage: CIImage) -> CIImage? {
        // Create kernel to filter pixels within HSV ranges
        let kernelCode = """
        kernel vec4 skinToneFilter(__sample pixel, float hMin1, float hMax1, float hMin2, float hMax2, float sMin, float sMax, float vMin, float vMax) {
            float h = pixel.r * 360.0;  // Convert 0-1 to 0-360
            float s = pixel.g * 100.0;  // Convert 0-1 to 0-100
            float v = pixel.b * 255.0;  // Convert 0-1 to 0-255

            // Check if pixel is within skin tone ranges
            bool hInRange = (h >= hMin1 && h <= hMax1) || (h >= hMin2 && h <= hMax2);
            bool sInRange = (s >= sMin && s <= sMax);
            bool vInRange = (v >= vMin && v <= vMax);

            float result = (hInRange && sInRange && vInRange) ? 1.0 : 0.0;

            return vec4(result, result, result, 1.0);
        }
        """

        guard let kernel = CIColorKernel(source: kernelCode) else {
            return nil
        }

        return kernel.apply(
            extent: hsvImage.extent,
            arguments: [
                hsvImage,
                hueRange1.min, hueRange1.max,
                hueRange2.min, hueRange2.max,
                saturationRange.min, saturationRange.max,
                valueRange.min, valueRange.max
            ]
        )
    }

    // MARK: - Private Methods - Morphological Operations

    /// Apply morphological operations sequence: dilate → erode → dilate
    /// This sequence (morphological closing) removes noise and smooths contours
    /// From Posner et al. (2012) Section III.1
    /// - Parameter image: Binary mask image
    /// - Returns: Processed binary mask with reduced noise
    private func applyMorphologicalOps(_ image: CIImage) -> CIImage {
        var result = image

        // Dilate: Expand white regions (connect nearby pixels)
        result = applyDilate(result, kernelSize: morphKernelSize)

        // Erode: Shrink white regions (remove small noise)
        result = applyErode(result, kernelSize: morphKernelSize)

        // Dilate again: Restore size and smooth boundaries
        result = applyDilate(result, kernelSize: morphKernelSize)

        return result
    }

    /// Dilate operation - expand white regions in binary mask
    /// Morphological dilation: max(neighborhood pixels)
    /// - Parameters:
    ///   - image: Input binary mask
    ///   - kernelSize: Size of morphological kernel (e.g., 5 for 5x5)
    /// - Returns: Dilated image
    private func applyDilate(_ image: CIImage, kernelSize: Int) -> CIImage {
        // Use CIMorphologyMaximum for dilation
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
    ///   - kernelSize: Size of morphological kernel (e.g., 5 for 5x5)
    /// - Returns: Eroded image
    private func applyErode(_ image: CIImage, kernelSize: Int) -> CIImage {
        // Use CIMorphologyMinimum for erosion
        guard let filter = CIFilter(name: "CIMorphologyMinimum") else {
            return image
        }

        filter.setValue(image, forKey: kCIInputImageKey)
        filter.setValue(Float(kernelSize), forKey: kCIInputRadiusKey)

        return filter.outputImage ?? image
    }

    // MARK: - Private Methods - Contour Detection

    /// Find the largest hand contour in binary mask
    /// Uses connected component analysis to find regions
    /// - Parameters:
    ///   - image: Binary mask image after morphological operations
    ///   - originalSize: Size of original camera frame
    /// - Returns: Bounding box of largest contour (hand ROI), or nil if no valid contour found
    private func findHandContour(_ image: CIImage, originalSize: CGRect) -> CGRect? {
        // Convert CIImage to CVPixelBuffer for pixel-level analysis
        guard let pixelBuffer = pixelBufferFromCIImage(image) else {
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

        // Find bounding box of white pixels (simple contour approximation)
        var minX = width
        var maxX = 0
        var minY = height
        var maxY = 0
        var pixelCount = 0

        for y in 0..<height {
            for x in 0..<width {
                let offset = y * bytesPerRow + x * 4
                let pixelPtr = baseAddress.advanced(by: offset).assumingMemoryBound(to: UInt8.self)

                // Check if pixel is white (skin region)
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

        // Check if enough pixels found (minimum hand area)
        guard pixelCount >= minHandArea else {
            return nil
        }

        // Create bounding box
        let boundingBox = CGRect(
            x: CGFloat(minX),
            y: CGFloat(minY),
            width: CGFloat(maxX - minX),
            height: CGFloat(maxY - minY)
        )

        // Validate bounding box
        guard boundingBox.width > 50 && boundingBox.height > 50 else {
            return nil
        }

        return boundingBox
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
