# Build and Test Command

Quick command to build the app and run tests in one go.

## Usage
```
/build-test [options]
```

## Options
- `--simulator` (default): Run tests on simulator
- `--device`: Run tests on connected device
- `--coverage`: Include code coverage report
- `--verbose`: Detailed output
- `--performance`: Run performance tests only
- `--quick`: Skip slow tests, just build + quick tests

## Examples

### Quick build and test
```
/build-test --quick
```

### Full test with coverage
```
/build-test --coverage
```

### Performance benchmarking
```
/build-test --performance --device
```

### Device testing
```
/build-test --device --verbose
```

## What It Does
1. Cleans previous build artifacts
2. Builds the project for target (simulator/device)
3. Runs all tests (or filtered tests)
4. Generates code coverage report (if requested)
5. Displays results summary

## Expected Output
```
Building for iOS Simulator...
✅ Build successful

Running tests...
✅ 47 tests passed
⚠️ 2 tests skipped
❌ 0 tests failed

Code Coverage: 78%

Total time: 45s
```

## Common Issues

**Build fails**: Check Xcode is installed
**Simulator not found**: Run `xcrun simctl list` to see available simulators
**Tests timeout**: Try `--quick` to run faster subset

## Integration with Development Workflow

Use this during:
- Feature development (after code changes)
- Before committing (verify no regressions)
- Performance investigation (with --performance)
- Release preparation (full suite with coverage)
