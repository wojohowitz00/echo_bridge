# Xcode Integration MCP Configuration

## Overview
This MCP server integration provides tools for managing Xcode builds, running tests, managing simulators, and deploying to devices.

## Available Commands

### Build Management
```bash
# Build the project
xcode build --scheme VirtualKeyboardApp --destination generic/platform=iOS

# Build for device
xcode build-device --scheme VirtualKeyboardApp

# Build for simulator
xcode build-simulator --scheme VirtualKeyboardApp

# Clean build
xcode clean --scheme VirtualKeyboardApp
```

### Test Execution
```bash
# Run all tests
xcode test --scheme VirtualKeyboardApp --destination 'platform=iOS Simulator,name=iPhone 14'

# Run specific test
xcode test --scheme VirtualKeyboardApp --test VirtualKeyboardAppTests/HandDetectorTests

# Run with coverage
xcode test --scheme VirtualKeyboardApp --code-coverage

# Performance tests
xcode test --scheme VirtualKeyboardApp --test-plan PerformanceTests
```

### Simulator Management
```bash
# List available simulators
xcode list-simulators

# Boot simulator
xcode boot-simulator --name 'iPhone 14'

# Shutdown simulator
xcode shutdown-simulator --name 'iPhone 14'

# Install app on simulator
xcode install-app --bundle VirtualKeyboardApp.app --simulator 'iPhone 14'

# Launch app on simulator
xcode launch-app --bundle-id com.virtualKeyboard.app --simulator 'iPhone 14'
```

### Device Management
```bash
# List connected devices
xcode list-devices

# Install on device
xcode install-device --bundle VirtualKeyboardApp.ipa

# Launch on device
xcode launch-device --bundle-id com.virtualKeyboard.app

# View device logs
xcode device-logs --bundle-id com.virtualKeyboard.app
```

### Performance Profiling
```bash
# Profile with Instruments
xcode profile --scheme VirtualKeyboardApp --template "Metal System Trace"

# Run performance tests
xcode test-performance --scheme VirtualKeyboardApp

# Generate performance report
xcode generate-performance-report
```

## Common Workflows

### Development Cycle
```bash
# 1. Build and test on simulator
xcode build-simulator --scheme VirtualKeyboardApp
xcode test --scheme VirtualKeyboardApp --destination 'platform=iOS Simulator,name=iPhone 14'

# 2. Run on actual device
xcode build-device --scheme VirtualKeyboardApp
xcode install-device --bundle VirtualKeyboardApp.ipa

# 3. View logs
xcode device-logs --bundle-id com.virtualKeyboard.app
```

### Performance Analysis
```bash
# 1. Profile with Metal (for GPU)
xcode profile --scheme VirtualKeyboardApp --template "Metal System Trace"

# 2. Profile CPU
xcode profile --scheme VirtualKeyboardApp --template "CPU"

# 3. Profile Memory
xcode profile --scheme VirtualKeyboardApp --template "Allocations"

# 4. Generate report
xcode generate-performance-report
```

### Pre-Release Checklist
```bash
# 1. Run all tests
xcode test --scheme VirtualKeyboardApp

# 2. Run with code coverage
xcode test --scheme VirtualKeyboardApp --code-coverage

# 3. Profile on device
xcode profile --device

# 4. Build for release
xcode build --scheme VirtualKeyboardApp --configuration Release
```

## Integration with Vision Pipeline

These commands help test the vision pipeline implementation:

```bash
# Test vision components
xcode test --test VirtualKeyboardAppTests/VisionTests

# Performance profile vision processing
xcode profile --scheme VirtualKeyboardApp --template "CPU" -- test-vision-pipeline

# Measure FPS on device
xcode launch-device --bundle-id com.virtualKeyboard.app --enable-debug-overlay
```

## Setup Requirements

1. Xcode 14.0+
2. iOS 14.0+ deployment target
3. Swift 5.7+
4. Connected device or running simulator

## Troubleshooting

### Build Failures
```bash
xcode clean --scheme VirtualKeyboardApp
xcode build --scheme VirtualKeyboardApp --verbose
```

### Test Failures
```bash
# Run with verbose output
xcode test --scheme VirtualKeyboardApp --verbose

# Run specific failing test
xcode test --scheme VirtualKeyboardApp --test <test_name>
```

### Simulator Issues
```bash
# Reset simulator
xcrun simctl erase all

# Boot specific simulator
xcode boot-simulator --name 'iPhone 14' --force-new
```

## Default Configuration
- Target Simulator: iPhone 14 Pro Max (iOS 17)
- Target Device: iPhone 12+ running iOS 15+
- Build Configuration: Debug (for development)
- Test Configuration: Full test suite with code coverage
