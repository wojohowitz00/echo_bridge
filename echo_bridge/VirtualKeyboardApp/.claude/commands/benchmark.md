# Benchmark Command

Run performance benchmarking suite for the vision pipeline and UI.

## Usage
```
/benchmark [test_type] [options]
```

## Test Types
- `vision` (default): Vision pipeline performance
- `ui`: UI rendering and responsiveness
- `full`: Complete system benchmark
- `accuracy`: Touch accuracy against test dataset

## Options
- `--device`: Run on physical device (recommended)
- `--simulator`: Run on simulator
- `--output <file>`: Save results to file (JSON/CSV)
- `--compare <baseline>`: Compare against baseline results
- `--repeat <n>`: Run test n times for averaging

## Examples

### Vision pipeline benchmark
```
/benchmark vision --device --repeat 3
```

### Full system benchmark with comparison
```
/benchmark full --device --output results.json --compare baseline.json
```

### Accuracy testing
```
/benchmark accuracy --repeat 5
```

### UI responsiveness test
```
/benchmark ui --device
```

## Output Metrics

### Vision Pipeline
- FPS (frames per second)
- Latency (end-to-end camera to touch event)
- Memory usage
- CPU usage
- Thermal state transitions

### UI Rendering
- Frame time (milliseconds)
- Dropped frames
- Touch feedback latency
- Scroll smoothness (if applicable)

### Touch Accuracy
- Overall accuracy percentage
- False positive rate
- False negative rate
- Confidence score statistics

### Full System
- Complete pipeline latency
- Memory footprint
- Battery drain rate
- Thermal throttling threshold

## Sample Output
```
Vision Pipeline Benchmark Results:
================================

FPS:                    28.4 (target: 15+) ✅
Latency:                34ms (target: <100ms) ✅
Memory:                 142MB (target: <150MB) ✅
CPU:                    18% average
Thermal:                Nominal

Touch Accuracy:         96% (target: 95%+) ✅
- False Positives:      2
- False Negatives:      2
- Avg Confidence:       0.87

Test Duration:          5 minutes
Device:                 iPhone 14 Pro Max
iOS Version:            17.0

Status: PASS ✅
```

## Comparison Report
When using `--compare`, generates a comparison:

```
Comparison to Baseline:
======================

Metric              Current  Baseline  Change
--------------------------------------------
FPS                 28.4     27.1      +4.8%
Latency             34ms     38ms      -10.5%
Memory              142MB    139MB     +2.2%
Touch Accuracy      96%      95%       +1%

Overall: Better performance! 📈
```

## Integration Points

Used for:
- Validating optimization changes
- Tracking performance regressions
- Benchmarking against paper specifications
- Profiling for hot spots
- Comparing device vs simulator results

## Paper Specifications
Targets based on research papers:
- Posner et al. (2012): 95%+ accuracy
- Borade et al. (2016): Real-time processing
- Apple: 15+ fps minimum, <100ms latency
