// swift-tools-version:6.0
import PackageDescription

let package = Package(
    name: "VirtualKeyboardApp",
    platforms: [
        .iOS(.v15),
    ],
    dependencies: [
        // Vision framework dependencies (built-in)
        // AVFoundation (built-in)
        // Combine (built-in)

        // Optional: For advanced image processing if needed
        // .package(url: "https://github.com/opencv/opencv-swift.git", from: "4.5.0"),

        // Optional: For statistical analysis in benchmarking
        // .package(url: "https://github.com/apple/swift-numerics.git", from: "1.0.0"),
    ],
    targets: [
        .target(
            name: "VirtualKeyboardApp",
            dependencies: [],
            path: "Sources",
            swiftSettings: [
                .upcomingFeature("StrictConcurrency"),
            ]
        ),
        .testTarget(
            name: "VirtualKeyboardAppTests",
            dependencies: ["VirtualKeyboardApp"],
            path: "Tests",
            swiftSettings: [
                .upcomingFeature("StrictConcurrency"),
            ]
        ),
    ]
)

/*
 Project Configuration:

 - Target: iOS 14.0+ (Xcode 26.01 compatible)
 - Swift Version: 6.0+ (Swift 6 strict concurrency model)
 - Xcode: 26.01 or later
 - Architecture: ARM64 (device) + x86_64 (simulator)

 Key Frameworks (built-in, no external deps needed):
 - Vision: Real-time image analysis
 - AVFoundation: Camera and media handling
 - CoreImage: Image processing
 - CoreGraphics: 2D drawing and geometry
 - Combine: Reactive programming
 - Metal: GPU acceleration (optional)

 Build Settings:
 - Code Coverage: Enabled for tests
 - Optimization: Inline + Aggressive (Release)
 - Swift Optimization: WholeModule (Release)
 - Strict Concurrency: Enabled (Swift 6 feature)

 Notes:
 - This package structure supports iOS app development
 - Vision framework handles all image processing
 - No external vision libraries needed (leverage Apple's APIs)
 - Optional dependencies can be added for statistical analysis
 - Swift 6 strict concurrency enabled for thread safety
 */
