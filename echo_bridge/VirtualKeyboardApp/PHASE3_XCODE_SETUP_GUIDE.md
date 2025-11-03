# Phase 3: Xcode Project Setup & Implementation Guide

## Overview

This guide provides step-by-step instructions for creating a native iOS Xcode project and integrating the complete Virtual Keyboard application for device testing and optimization.

**Objective**: Move from SPM package structure to production-ready iOS Xcode project
**Target**: iPhone 12+, iOS 14+
**Estimated Time**: 30-45 minutes for project setup

---

## Part 1: Create iOS Xcode Project

### Step 1.1: Open Xcode and Create New Project

```
1. Open Xcode (Applications > Xcode or Command+Space > "Xcode")
2. File > New > Project
3. Select "iOS" tab
4. Choose "App" template
5. Click "Next"
```

### Step 1.2: Configure Project Details

Fill in the following information:

| Field | Value |
|-------|-------|
| Product Name | `VirtualKeyboardApp` |
| Team | Your Apple Team (create free if needed) |
| Organization Identifier | `com.yourname` |
| Bundle Identifier | `com.yourname.virtualkeyboard` |
| Language | **Swift** |
| User Interface | **SwiftUI** |
| Use Core Data | **NO** (uncheck) |
| Include Tests | **YES** (check) |

**Click "Next"**

### Step 1.3: Select Project Location

1. Choose a location to save the project
2. **Recommended**: Save in same directory as Swift Package
   - Path: `/Users/richardyu/Library/Mobile Documents/com~apple~CloudDocs/1 Projects/echo_bridge/`
   - This allows easy reference to SPM sources
3. **Uncheck** "Create Git repository" (if not needed)
4. Click "Create"

---

## Part 2: Configure Build Settings

### Step 2.1: Set Deployment Target

1. In Xcode: Select **VirtualKeyboardApp** project (left sidebar)
2. Select **VirtualKeyboardApp** target
3. Go to **Build Settings** tab
4. Search for "Minimum Deployments"
5. Set **iOS Minimum Deployment Target** to `14.0`

### Step 2.2: Add Required Frameworks

1. Go to **Build Phases** tab
2. Expand **Link Binary With Libraries**
3. Click **+** button
4. Add the following frameworks:
   - ✅ AVFoundation
   - ✅ CoreImage
   - ✅ Vision
   - ✅ Combine (automatically included with iOS 13+)

**All should be marked "Status: Optional" (OK for this project)**

### Step 2.3: Configure Info.plist

1. Select **Info.plist** in project navigator
2. Add the following key:
   ```
   Key: Privacy - Camera Usage Description
   Value: "This app needs camera access to detect your hand and enable touch input on any flat surface."
   ```

---

## Part 3: Import Vision Pipeline Source Code

### Step 3.1: Copy Vision Components

1. **In Finder**, navigate to:
   ```
   /Users/richardyu/Library/Mobile Documents/com~apple~CloudDocs/1 Projects/echo_bridge/VirtualKeyboardApp/Sources/Vision/
   ```

2. **Select and copy** all files:
   - HandDetector.swift
   - FingertipDetector.swift
   - ShadowAnalyzer.swift
   - TouchValidator.swift

3. **In Xcode**, right-click on project > **Add Files to "VirtualKeyboardApp"**

4. **Select the Vision folder** from the Finder location above

5. **Ensure**:
   - ☑ Copy items if needed
   - ☑ Create groups
   - ✅ Add to target: VirtualKeyboardApp
   - Click **Add**

### Step 3.2: Copy Data Models

1. Repeat the process for Models:
   ```
   /Users/richardyu/Library/Mobile Documents/com~apple~CloudDocs/1 Projects/echo_bridge/VirtualKeyboardApp/Sources/Models/
   ```

2. Copy files:
   - HandData.swift
   - TouchEvent.swift
   - KeyboardKey.swift

3. In Xcode: **Add Files** > select Models folder

---

## Part 4: Create Core Components

### Step 4.1: Create VisionPipelineManager.swift

In Xcode project navigator:
1. Right-click **VirtualKeyboardApp** folder
2. **New File** > **Swift File**
3. Name: `VisionPipelineManager`
4. Target: ✅ VirtualKeyboardApp

**Copy the following implementation**:

```swift
import Foundation
import AVFoundation
import Combine

/// Central orchestrator for the complete vision pipeline
class VisionPipelineManager: NSObject, ObservableObject, AVCaptureVideoDataOutputSampleBufferDelegate {
    @Published var currentHandData: HandData?
    @Published var currentTouchValidation: TouchValidationResult = .idle
    @Published var averageFPS: Float = 0
    @Published var averageLatency: TimeInterval = 0
    @Published var isProcessing = false

    private let handDetector = HandDetector()
    private let fingertipDetector = FingertipDetector()
    private let shadowAnalyzer = ShadowAnalyzer()
    private let touchValidator = TouchValidator()

    private var captureSession: AVCaptureSession?
    private var videoOutput: AVCaptureVideoDataOutput?

    private let processingQueue = DispatchQueue(label: "com.virtualkeyboard.processing", qos: .userInitiated)

    private var frameTimestamps: [TimeInterval] = []
    private var latencyMeasurements: [TimeInterval] = []
    private var referenceFrame: CVPixelBuffer?

    override init() {
        super.init()
        setupCaptureSession()
    }

    private func setupCaptureSession() {
        captureSession = AVCaptureSession()
        guard let session = captureSession else { return }

        session.beginConfiguration()

        // Configure session
        if session.canSetSessionPreset(.vga640x480) {
            session.sessionPreset = .vga640x480
        }

        // Add camera input
        guard let camera = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .front) else {
            return
        }

        do {
            let input = try AVCaptureDeviceInput(device: camera)
            if session.canAddInput(input) {
                session.addInput(input)
            }
        } catch {
            print("Error adding camera input: \(error)")
        }

        // Add video output
        videoOutput = AVCaptureVideoDataOutput()
        videoOutput?.setSampleBufferDelegate(self, queue: processingQueue)
        videoOutput?.videoSettings = [
            kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA
        ]

        if let output = videoOutput, session.canAddOutput(output) {
            session.addOutput(output)
        }

        session.commitConfiguration()
    }

    func startProcessing() {
        guard let session = captureSession, !session.isRunning else { return }
        DispatchQueue.global(qos: .userInitiated).async {
            session.startRunning()
            DispatchQueue.main.async {
                self.isProcessing = true
            }
        }
    }

    func stopProcessing() {
        guard let session = captureSession, session.isRunning else { return }
        session.stopRunning()
        DispatchQueue.main.async {
            self.isProcessing = false
        }
    }

    func captureReferenceFrame(_ pixelBuffer: CVPixelBuffer) {
        referenceFrame = pixelBuffer
    }

    // MARK: - AVCaptureVideoDataOutputSampleBufferDelegate

    func captureOutput(_ output: AVCaptureOutput,
                       didOutput sampleBuffer: CMSampleBuffer,
                       from connection: AVCaptureConnection) {
        let startTime = Date()

        guard let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }

        // Run vision pipeline
        let result = runVisionPipeline(pixelBuffer)

        let latency = Date().timeIntervalSince(startTime)
        recordMetrics(latency: latency)

        DispatchQueue.main.async {
            self.currentHandData = result.handData
            self.currentTouchValidation = result.touchValidation
        }
    }

    private func runVisionPipeline(_ pixelBuffer: CVPixelBuffer) -> (handData: HandData?, touchValidation: TouchValidationResult) {
        // Step 1: Hand Detection
        let handData = handDetector.detectHand(pixelBuffer: pixelBuffer)

        guard let hand = handData, hand.confidence > 0.5 else {
            return (nil, .idle)
        }

        // Step 2: Fingertip Detection
        let fingertip = fingertipDetector.detectFingertip(
            pixelBuffer: pixelBuffer,
            handRegion: hand.region
        )

        guard let fp = fingertip else {
            return (hand, .hoverState)
        }

        // Step 3: Shadow Analysis
        let shadowTip: (x: Float, y: Float)?
        if let refFrame = referenceFrame {
            shadowTip = shadowAnalyzer.analyzeShadow(
                currentFrame: pixelBuffer,
                referenceFrame: refFrame,
                region: hand.region
            )
        } else {
            shadowTip = nil
        }

        // Step 4: Touch Validation
        let touchValidation: TouchValidationResult
        if let shadow = shadowTip {
            let distance = sqrt(pow(fp.x - shadow.x, 2) + pow(fp.y - shadow.y, 2))
            touchValidation = touchValidator.validateTouch(distance: distance, confidence: hand.confidence)
        } else {
            touchValidation = .lowConfidence
        }

        return (hand, touchValidation)
    }

    private func recordMetrics(latency: TimeInterval) {
        frameTimestamps.append(Date().timeIntervalSince1970)
        latencyMeasurements.append(latency)

        // Keep only last 60 frames worth of data
        if frameTimestamps.count > 60 {
            frameTimestamps.removeFirst()
            latencyMeasurements.removeFirst()
        }

        // Calculate FPS
        if frameTimestamps.count > 1 {
            let timeSpan = frameTimestamps.last! - frameTimestamps.first!
            if timeSpan > 0 {
                let fps = Float(frameTimestamps.count) / Float(timeSpan)
                DispatchQueue.main.async {
                    self.averageFPS = fps
                }
            }
        }

        // Calculate average latency
        if !latencyMeasurements.isEmpty {
            let avgLatency = latencyMeasurements.reduce(0, +) / Double(latencyMeasurements.count)
            DispatchQueue.main.async {
                self.averageLatency = avgLatency
            }
        }
    }

    deinit {
        stopProcessing()
    }
}
```

### Step 4.2: Create InputStateManager.swift

**New File** > `InputStateManager.swift`

```swift
import Foundation
import Combine

enum TouchInputState {
    case idle
    case hovering
    case touching
    case invalid
}

class InputStateManager: ObservableObject {
    @Published var touchState: TouchInputState = .idle
    @Published var isInputEnabled = true

    private var lastTouchTime: Date?
    private let debounceInterval: TimeInterval = 0.05 // 50ms debounce

    func processTouchEvent(_ validation: TouchValidationResult) {
        guard isInputEnabled else {
            touchState = .idle
            return
        }

        switch validation {
        case .touchValid:
            // Check debounce
            let now = Date()
            if let lastTime = lastTouchTime, now.timeIntervalSince(lastTime) < debounceInterval {
                return // Ignore debounced touch
            }
            lastTouchTime = now
            touchState = .touching

        case .hoverState:
            touchState = .hovering

        default:
            touchState = .idle
        }
    }

    func reset() {
        touchState = .idle
        lastTouchTime = nil
    }

    func disableInput() {
        isInputEnabled = false
        touchState = .idle
    }

    func enableInput() {
        isInputEnabled = true
    }
}
```

### Step 4.3: Create PerformanceMonitor.swift

**New File** > `PerformanceMonitor.swift`

```swift
import Foundation
import Combine

class PerformanceMonitor: ObservableObject {
    @Published var averageFPS: Double = 0
    @Published var averageLatency: Double = 0
    @Published var peakMemoryUsage: Double = 0
    @Published var averageMemoryUsage: Double = 0

    private var frameTimestamps: [Date] = []
    private var latencyMeasurements: [Double] = []
    private var memoryMeasurements: [Double] = []

    func recordFrameTimestamp() {
        frameTimestamps.append(Date())

        if frameTimestamps.count > 120 {
            frameTimestamps.removeFirst()
        }

        calculateFPS()
    }

    func recordLatency(_ latency: TimeInterval) {
        latencyMeasurements.append(latency)

        if latencyMeasurements.count > 120 {
            latencyMeasurements.removeFirst()
        }

        calculateAverageLatency()
    }

    func recordMemoryUsage(_ usage: Double) {
        memoryMeasurements.append(usage)
        peakMemoryUsage = max(peakMemoryUsage, usage)

        if memoryMeasurements.count > 120 {
            memoryMeasurements.removeFirst()
        }

        calculateAverageMemory()
    }

    private func calculateFPS() {
        guard frameTimestamps.count > 1 else { return }

        let timeSpan = frameTimestamps.last!.timeIntervalSince(frameTimestamps.first!)
        if timeSpan > 0 {
            averageFPS = Double(frameTimestamps.count) / timeSpan
        }
    }

    private func calculateAverageLatency() {
        guard !latencyMeasurements.isEmpty else { return }
        averageLatency = latencyMeasurements.reduce(0, +) / Double(latencyMeasurements.count)
    }

    private func calculateAverageMemory() {
        guard !memoryMeasurements.isEmpty else { return }
        averageMemoryUsage = memoryMeasurements.reduce(0, +) / Double(memoryMeasurements.count)
    }
}
```

### Step 4.4: Create CameraManager.swift

**New File** > `CameraManager.swift`

```swift
import Foundation
import AVFoundation

class CameraManager: NSObject {
    static let shared = CameraManager()

    private var captureSession: AVCaptureSession?

    static func requestCameraPermission(completion: @escaping (Bool) -> Void) {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            completion(true)
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { granted in
                DispatchQueue.main.async {
                    completion(granted)
                }
            }
        case .denied, .restricted:
            completion(false)
        @unknown default:
            completion(false)
        }
    }

    static func isCameraAvailable() -> Bool {
        return AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .front) != nil
    }

    func startCapture(delegate: AVCaptureVideoDataOutputSampleBufferDelegate) {
        let session = AVCaptureSession()
        self.captureSession = session

        session.beginConfiguration()

        guard let camera = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .front) else {
            return
        }

        do {
            let input = try AVCaptureDeviceInput(device: camera)
            if session.canAddInput(input) {
                session.addInput(input)
            }
        } catch {
            print("Error: \(error)")
        }

        session.commitConfiguration()
    }

    func stopCapture() {
        captureSession?.stopRunning()
    }
}
```

---

## Part 5: Create UI Components

### Step 5.1: Replace ContentView.swift

In Xcode, select the default `ContentView.swift` and replace with:

```swift
import SwiftUI

struct ContentView: View {
    @StateObject var visionManager = VisionPipelineManager()
    @StateObject var inputState = InputStateManager()
    @StateObject var performanceMonitor = PerformanceMonitor()

    @State var cameraPermissionDenied = false
    @State var showDebugOverlay = false

    var body: some View {
        ZStack {
            VStack(spacing: 0) {
                CameraView(
                    handData: visionManager.currentHandData,
                    touchValidation: visionManager.currentTouchValidation
                )
                .frame(maxHeight: .infinity)

                KeyboardView(
                    touchState: inputState.touchState,
                    touchValidation: visionManager.currentTouchValidation
                )
                .frame(height: 150)
            }

            if showDebugOverlay {
                DebugOverlayView(
                    fps: visionManager.averageFPS,
                    latency: visionManager.averageLatency,
                    confidence: visionManager.currentHandData?.confidence ?? 0
                )
                .padding()
            }
        }
        .onAppear {
            CameraManager.requestCameraPermission { granted in
                if granted {
                    visionManager.startProcessing()
                } else {
                    cameraPermissionDenied = true
                }
            }
        }
        .onDisappear {
            visionManager.stopProcessing()
        }
        .onTapGesture(count: 3) {
            showDebugOverlay.toggle()
        }
        .sheet(isPresented: $cameraPermissionDenied) {
            PermissionDeniedView()
        }
    }
}

struct CameraView: View {
    let handData: HandData?
    let touchValidation: TouchValidationResult

    var body: some View {
        ZStack {
            Color.black

            VStack {
                Text("Hand Detected: \(handData != nil ? "Yes" : "No")")
                    .foregroundColor(.white)

                if let hand = handData {
                    Text("Confidence: \(String(format: "%.0f%%", hand.confidence * 100))")
                        .foregroundColor(.white)
                }

                Spacer()
            }
            .padding()
        }
    }
}

struct KeyboardView: View {
    let touchState: TouchInputState
    let touchValidation: TouchValidationResult

    var body: some View {
        VStack {
            HStack(spacing: 4) {
                ForEach(["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"], id: \.self) { key in
                    KeyButton(label: key, isActive: touchState == .touching)
                }
            }
            .padding(4)

            HStack(spacing: 4) {
                ForEach(["A", "S", "D", "F", "G", "H", "J", "K", "L"], id: \.self) { key in
                    KeyButton(label: key, isActive: touchState == .touching)
                }
            }
            .padding(4)

            HStack(spacing: 4) {
                ForEach(["Z", "X", "C", "V", "B", "N", "M"], id: \.self) { key in
                    KeyButton(label: key, isActive: touchState == .touching)
                }
            }
            .padding(4)
        }
        .background(Color.gray.opacity(0.3))
    }
}

struct KeyButton: View {
    let label: String
    let isActive: Bool

    var body: some View {
        Button(action: {}) {
            Text(label)
                .font(.system(.body, design: .default))
                .frame(maxWidth: .infinity)
                .padding(8)
                .background(isActive ? Color.green : Color.white)
                .foregroundColor(isActive ? .white : .black)
                .cornerRadius(4)
        }
    }
}

struct PermissionDeniedView: View {
    @Environment(\.dismiss) var dismiss

    var body: some View {
        VStack(spacing: 16) {
            Text("Camera Permission Required")
                .font(.headline)

            Text("This app needs camera access to detect your hand and enable touch input.")
                .foregroundColor(.gray)

            Button("Open Settings") {
                if let url = URL(string: UIApplication.openSettingsURLString) {
                    UIApplication.shared.open(url)
                }
            }
            .foregroundColor(.blue)

            Spacer()
        }
        .padding()
    }
}

struct DebugOverlayView: View {
    let fps: Float
    let latency: TimeInterval
    let confidence: Float

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Debug Info")
                .font(.headline)

            Text("FPS: \(String(format: "%.1f", fps))")
            Text("Latency: \(String(format: "%.0f", latency * 1000))ms")
            Text("Confidence: \(String(format: "%.0f%%", confidence * 100))")
        }
        .padding()
        .background(Color.black.opacity(0.7))
        .foregroundColor(.white)
        .cornerRadius(8)
    }
}

#Preview {
    ContentView()
}
```

---

## Part 6: Build and Test

### Step 6.1: Build the Project

1. **Product** > **Build** (or Command+B)
2. Wait for build to complete
3. Check for errors in the Issue Navigator

### Step 6.2: Run on Simulator

1. **Select simulator** from the device dropdown (top of Xcode)
2. **Product** > **Run** (or Command+R)
3. Allow a few moments for app to launch

---

## Part 7: Next Steps

Once the Xcode project is set up and running on simulator:

1. **Test on Physical Device**:
   - Connect iPhone 12+ with iOS 14+
   - Select device from device dropdown
   - Product > Run
   - Allow app to install

2. **Begin Phase 3 Testing**:
   - Follow procedures in `DEVICE_TESTING_GUIDE.md`
   - Run accuracy benchmarks
   - Profile performance
   - Optimize as needed

3. **Track Results**:
   - Document results in JSON format
   - Use CSV export from benchmarking tools
   - Compare against targets

---

## Troubleshooting

### Build Errors

**Error**: "Cannot find type in scope"
- **Solution**: Ensure all vision component files were added to Xcode target

**Error**: "Use of undeclared type 'AVCaptureSession'"
- **Solution**: Add AVFoundation framework (Build Phases > Link Binary With Libraries)

### Runtime Errors

**Error**: "NSCameraUsageDescription not found"
- **Solution**: Add Privacy - Camera Usage Description to Info.plist

**Error**: "App crashes on launch"
- **Solution**: Check console for detailed error messages; ensure CameraManager permissions are handled

### Device Connection Issues

**Issue**: Device not appearing in device dropdown
- **Solution**:
  1. Reconnect USB cable
  2. Trust device on iPhone (when prompted)
  3. Restart Xcode if needed

---

## Summary

✅ **Xcode Project Setup Complete When**:
- Project builds without errors
- App runs on simulator
- Camera feed displays
- Hand detection initializes
- Debug overlay toggles with triple-tap

Next: Follow DEVICE_TESTING_GUIDE.md for comprehensive testing procedures.
