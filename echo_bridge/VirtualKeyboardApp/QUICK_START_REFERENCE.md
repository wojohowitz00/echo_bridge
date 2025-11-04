# Virtual Keyboard iOS App - Quick Reference Card

**Status**: ✅ Swift 6 Refactoring Complete → 🚀 Ready for Testing

---

## ⚡ Get Started in 5 Minutes

### 1️⃣ Verify Build (1 min)
```bash
cd "/Users/richardyu/Library/Mobile Documents/com~apple~CloudDocs/1 Projects/echo_bridge/VirtualKeyboardApp"
swift build
```
**Expected**: `✅ Build complete! (8.4s)`

### 2️⃣ Open Xcode (1 min)
```bash
open VirtualKeyboardApp/VirtualKeyboardApp/VirtualKeyboardApp.xcodeproj
```

### 3️⃣ Configure Scheme (1 min)
- **Product** > **Scheme** > **Edit Scheme**
- Select any available iOS simulator or connected device
- Click **Close**

### 4️⃣ Build & Run (2 min)
- **Cmd+B** to build
- **Cmd+R** to run on simulator
- Grant camera permission when prompted

**Expected Result**: Black screen with "Hand Detected: No" text

---

## 📖 Documentation to Read

| Document | Time | Purpose |
|----------|------|---------|
| **SWIFT6_REFACTORING_COMPLETE.md** | 10 min | Technical details of what changed |
| **PHASE3_READY_TO_START.md** | 10 min | Project overview & success criteria |
| **DEVICE_TESTING_GUIDE.md** | Reference | Complete testing procedures |
| **PHASE3_OVERVIEW.md** | Reference | Performance targets & optimization |

**Recommended Reading Order**:
1. This card (now) ✓
2. SWIFT6_REFACTORING_COMPLETE.md (technical)
3. PHASE3_READY_TO_START.md (planning)
4. DEVICE_TESTING_GUIDE.md (while testing)

---

## ✅ Verification Checklist

After running the app:

- [ ] Build succeeds without errors
- [ ] Xcode opens project without issues
- [ ] App launches on simulator
- [ ] Camera permission request appears
- [ ] Shows "Hand Detected: No" when hand not visible
- [ ] Shows "Hand Detected: Yes" when hand in frame
- [ ] Triple-tap shows debug overlay (FPS, latency)
- [ ] Keyboard keys highlight based on hand position

---

## 🧪 Quick Testing (10 minutes)

### Test 1: Hand Detection
1. Run app on simulator
2. Move hand/cursor in and out of view
3. Should show "Hand Detected: Yes/No" based on visibility
4. **Pass Criteria**: Correct detection state

### Test 2: Fingertip Tracking
1. Show finger clearly to camera
2. Move finger around
3. App should track fingertip position
4. **Pass Criteria**: Smooth tracking without lag

### Test 3: Debug Overlay
1. Triple-tap screen to show debug info
2. Note FPS (target: 15+ fps)
3. Note Latency (target: <100ms)
4. Note Confidence (target: 70%+)
5. **Pass Criteria**: All metrics within targets

### Test 4: Keyboard Response
1. Move hand over keyboard area
2. Keys should highlight based on position
3. Keys should turn green when hand detected over them
4. **Pass Criteria**: Accurate key highlighting

---

## 🐛 Troubleshooting (Common Issues)

### Issue: "No supported platforms" in Xcode
**Fix**: Follow Step 3 (Configure Scheme) above

### Issue: Build fails with Swift error
**Fix**: Verify Xcode 16+ is installed
```bash
xcode-select --print-path  # Should show /Applications/Xcode.app/...
```

### Issue: "CoreSimulator is out of date" warning
**Status**: Non-blocking - can still run on device
**Fix**: Update to latest Xcode from App Store

### Issue: App shows black screen
**Expected**: Camera feed takes a moment to load
**Fix**: Wait 2-3 seconds, move hand in front of camera

### Issue: Camera permission denied
**Fix**:
- Simulator: Product > Reset Contents and Settings
- Device: Settings > VirtualKeyboardApp > Camera > Allow

---

## 📋 Success Criteria (Must Pass All)

### Build & Code
- ✅ Swift Package Manager builds cleanly
- ✅ Xcode project opens without errors
- ✅ Zero compilation errors in Xcode
- ✅ All tests passing (swift test)

### Functionality
- ✅ App launches successfully
- ✅ Camera permission works
- ✅ Hand detection responds correctly
- ✅ Keyboard displays and highlights keys

### Performance (Target)
- ✅ Frame rate: 15+ fps
- ✅ Latency: <100ms
- ✅ Memory: <20MB
- ✅ CPU: <50% single core

---

## 🚀 Next Phase: Device Testing (Days 2-5)

After verifying the above, follow:

**Read**: PHASE3_READY_TO_START.md → DEVICE_TESTING_GUIDE.md

**Day 1**: Xcode setup & basic testing (this card)
**Day 2**: Accuracy benchmarking (100+ touches)
**Day 3**: Performance profiling with Instruments
**Day 4**: Stress testing (2-hour run)
**Day 5**: Sign-off & release preparation

---

## 💾 Key Files (Don't Delete)

### Source Code (All needed for build):
```
VirtualKeyboardApp/
├── Sources/Vision/
│   ├── VisionPipelineManager.swift     ← Main orchestrator
│   ├── HandDetector.swift              ← Hand detection
│   ├── FingertipDetector.swift         ← Fingertip tracking
│   ├── ShadowAnalyzer.swift            ← Shadow detection
│   └── TouchValidator.swift            ← Touch validation
├── Sources/Models/
│   ├── HandData.swift
│   ├── TouchEvent.swift
│   └── KeyboardKey.swift
├── Sources/Core/
│   ├── CameraManager.swift
│   ├── InputStateManager.swift
│   ├── PerformanceMonitor.swift
│   └── ContentView.swift
└── Package.swift                        ← Project manifest
```

### Documentation (Reference while testing):
```
├── README.md                            ← Project overview
├── SWIFT6_REFACTORING_COMPLETE.md      ← This session's work
├── PHASE3_READY_TO_START.md            ← Phase 3 overview
├── DEVICE_TESTING_GUIDE.md             ← Testing procedures
├── PHASE3_OVERVIEW.md                  ← Performance targets
└── QUICK_START_REFERENCE.md            ← This card
```

---

## 🔗 Command Quick Reference

```bash
# Build
swift build
xcodebuild -scheme VirtualKeyboardApp

# Test
swift test

# Open in Xcode
open VirtualKeyboardApp/VirtualKeyboardApp/VirtualKeyboardApp.xcodeproj

# Git
git status                              # Check status
git log --oneline -5                    # View recent commits
git push origin main                    # Push to remote (if configured)

# In Xcode
Cmd+B  →  Build
Cmd+R  →  Run
Cmd+U  →  Test
Cmd+I  →  Profile
Cmd+/  →  Toggle comment
```

---

## 📞 Help & Support

### Build Issues
- Check: Xcode 16+ installed
- Check: Swift 6 available
- Reference: SWIFT6_REFACTORING_COMPLETE.md

### Testing Issues
- Read: DEVICE_TESTING_GUIDE.md Part 9 (Troubleshooting)
- Reference: Success criteria above

### Performance Questions
- Reference: PHASE3_OVERVIEW.md
- Read: DEVICE_TESTING_GUIDE.md Part 5

### Code Questions
- Check: .claude/CLAUDE.md (architecture)
- Review: Inline comments in source files

---

## 📊 What Changed (Swift 6 Refactoring)

**iOS 15.0+**: Increased from iOS 14.0
**@MainActor**: Added to UI-affecting classes
**Sendable**: All data models updated for strict concurrency
**async/await**: Replaced callbacks throughout
**Build**: Compiles cleanly in 8.4 seconds

See SWIFT6_REFACTORING_COMPLETE.md for full details.

---

## ⏱️ Time Estimates

| Task | Time |
|------|------|
| Verify build | 1 min |
| Open Xcode | 1 min |
| Configure scheme | 1 min |
| Build & run | 2 min |
| Quick test | 10 min |
| **Total Baseline** | **15 min** |
| + Device deployment | 10 min |
| + Full testing (Day 1-5) | 5 days |

---

## 🎯 Immediate Next Steps

### Right Now (Next 5 minutes):
1. Run `swift build` to verify
2. Open project in Xcode
3. Build and run on simulator
4. See app launch with camera feed

### Next 1-2 hours:
1. Read SWIFT6_REFACTORING_COMPLETE.md
2. Read PHASE3_READY_TO_START.md
3. Deploy to physical device (if available)
4. Run through DEVICE_TESTING_GUIDE.md Part 2-3

### Days 2-5:
1. Follow DEVICE_TESTING_GUIDE.md Part 4-10
2. Collect metrics and data
3. Validate against success criteria
4. Prepare release build

---

**Generated**: November 4, 2025
**Status**: ✅ Swift 6 Complete → 🚀 Ready to Test
**Estimated Time to Start**: 5 minutes
**Estimated Time to Phase 3 Complete**: 5 days

👉 **Next Action**: Run `swift build` and open in Xcode! 🚀
