# Summon Vision Specialist Command

Invoke the Vision Processing Specialist agent to work on the vision pipeline.

## Usage
```
/summon-vision [task] [context]
```

## Tasks

### Implementation Tasks
- `implement-hand-detector`: Enhance HandDetector.swift
- `implement-fingertip`: Enhance FingertipDetector.swift
- `implement-shadow`: Enhance ShadowAnalyzer.swift
- `integrate-pipeline`: Wire up VisionPipelineManager
- `optimize-performance`: Profile and optimize
- `add-tests`: Create vision component tests

### Review Tasks
- `review-hand-detection`: Review hand detection algorithm
- `review-accuracy`: Review touch accuracy metrics
- `review-performance`: Review FPS and latency

## Examples

### Start hand detection implementation
```
/summon-vision implement-hand-detector
```

### Debug performance issues
```
/summon-vision optimize-performance

Context: FPS dropping below 15 on device
```

### Review accuracy results
```
/summon-vision review-accuracy

Context: Current accuracy is 92%, need to reach 95%
```

## What the Vision Specialist Does

1. **Analyzes the Request**
   - Reads current code state
   - Reviews relevant skills
   - Checks paper specifications

2. **Executes Task**
   - Implements or enhances code
   - Runs tests to validate
   - Profiles performance

3. **Reports Progress**
   - Code changes made
   - Test results
   - Metrics (FPS, accuracy)
   - Next steps

## Expected Timeline

- Hand Detection impl: 30-45 min
- Fingertip Detection impl: 30-45 min
- Shadow Analysis impl: 30-45 min
- Integration: 20-30 min
- Testing: 30-45 min
- Optimization: 30-60 min

## Key Parameters

The Vision Specialist has access to:
- `.claude/skills/virtual-keyboard-vision.md` (algorithm details)
- `Sources/Vision/*.swift` (implementation files)
- `Sources/Models/*.swift` (data structures)
- Papers in project root (Posner et al., Borade et al.)

## Success Criteria

Task is complete when:
✅ Code compiles without errors
✅ All unit tests pass (>80% coverage)
✅ Touch accuracy ≥95% on test dataset
✅ FPS ≥15 (device target)
✅ Latency <100ms
✅ Memory <150MB

## Communication

Vision Specialist will:
- Ask clarifying questions about requirements
- Show code changes for review
- Report metrics and benchmarks
- Identify blockers or issues
- Suggest optimizations

## Integration with Other Agents

Coordinates with:
- **iOS Expert**: Takes CameraManager input, provides HandData output
- **Testing Agent**: Validates implementation, benchmarks accuracy

## Starting Now

Ready to start vision implementation. Use:
```
/summon-vision implement-hand-detector
```

To begin HandDetector enhancement with HSV color segmentation.
