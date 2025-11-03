import Foundation

/// Comprehensive accuracy benchmarking framework for the Virtual Keyboard vision pipeline
/// Tests touch detection accuracy against ground truth data

// MARK: - Benchmark Data Structures

/// Ground truth annotation for a single touch event
struct TouchAnnotation {
    /// Frame number in the video sequence
    let frameId: Int

    /// Ground truth X coordinate (camera frame coordinates)
    let groundTruthX: Float

    /// Ground truth Y coordinate (camera frame coordinates)
    let groundTruthY: Float

    /// Expected keyboard key (if applicable)
    let expectedKey: KeyboardKey?

    /// Lighting condition (low, normal, bright)
    let lightingCondition: String

    /// Human hand size category (small, medium, large)
    let handSize: String

    /// Expected touch validation result
    let expectedResult: TouchValidationResult
}

/// Test dataset containing multiple ground truth annotations
struct TestDataset {
    /// Unique identifier for this dataset
    let datasetId: String

    /// Device model used for recording
    let deviceModel: String

    /// iOS version used for recording
    let iosVersion: String

    /// All ground truth annotations in sequence order
    let annotations: [TouchAnnotation]

    /// Metadata about the dataset
    var description: String {
        """
        Dataset: \(datasetId)
        Device: \(deviceModel)
        iOS: \(iosVersion)
        Samples: \(annotations.count)
        """
    }
}

// MARK: - Accuracy Metrics

/// Comprehensive accuracy metrics for evaluation
struct AccuracyMetrics {
    /// True positives: correctly detected touches
    let truePositives: Int

    /// False positives: incorrectly detected touches
    let falsePositives: Int

    /// False negatives: missed touches
    let falseNegatives: Int

    /// True negatives: correctly identified non-touches
    let trueNegatives: Int

    /// Precision: TP / (TP + FP)
    var precision: Double {
        let denominator = Double(truePositives + falsePositives)
        return denominator > 0 ? Double(truePositives) / denominator : 0
    }

    /// Recall: TP / (TP + FN)
    var recall: Double {
        let denominator = Double(truePositives + falseNegatives)
        return denominator > 0 ? Double(truePositives) / denominator : 0
    }

    /// F1 Score: 2 * (Precision * Recall) / (Precision + Recall)
    var f1Score: Double {
        let sum = precision + recall
        return sum > 0 ? 2 * (precision * recall) / sum : 0
    }

    /// Accuracy: (TP + TN) / Total
    var accuracy: Double {
        let total = truePositives + falsePositives + falseNegatives + trueNegatives
        return total > 0 ? Double(truePositives + trueNegatives) / Double(total) : 0
    }

    /// False Positive Rate: FP / (FP + TN)
    var falsePositiveRate: Double {
        let denominator = Double(falsePositives + trueNegatives)
        return denominator > 0 ? Double(falsePositives) / denominator : 0
    }

    /// False Negative Rate: FN / (FN + TP)
    var falseNegativeRate: Double {
        let denominator = Double(falseNegatives + truePositives)
        return denominator > 0 ? Double(falseNegatives) / denominator : 0
    }

    /// Summary description
    var summary: String {
        """
        Accuracy Metrics Summary
        ─────────────────────────
        Precision:           \(String(format: "%.2f%%", precision * 100))
        Recall:              \(String(format: "%.2f%%", recall * 100))
        F1 Score:            \(String(format: "%.4f", f1Score))
        Accuracy:            \(String(format: "%.2f%%", accuracy * 100))
        False Positive Rate: \(String(format: "%.2f%%", falsePositiveRate * 100))
        False Negative Rate: \(String(format: "%.2f%%", falseNegativeRate * 100))

        Confusion Matrix
        ─────────────────────────
        True Positives:  \(truePositives)
        True Negatives:  \(trueNegatives)
        False Positives: \(falsePositives)
        False Negatives: \(falseNegatives)
        """
    }
}

// MARK: - Positional Accuracy Metrics

/// Metrics for evaluating fingertip and touch position accuracy
struct PositionalAccuracyMetrics {
    /// Individual position errors (in pixels)
    let positionErrors: [Float]

    /// Mean absolute error in pixels
    var meanAbsoluteError: Float {
        guard !positionErrors.isEmpty else { return 0 }
        return positionErrors.reduce(0, +) / Float(positionErrors.count)
    }

    /// Maximum error observed (in pixels)
    var maxError: Float {
        return positionErrors.max() ?? 0
    }

    /// Minimum error observed (in pixels)
    var minError: Float {
        return positionErrors.min() ?? 0
    }

    /// Standard deviation of errors
    var standardDeviation: Float {
        guard !positionErrors.isEmpty else { return 0 }
        let mean = meanAbsoluteError
        let variance = positionErrors.map { ($0 - mean) * ($0 - mean) }.reduce(0, +) / Float(positionErrors.count)
        return sqrt(variance)
    }

    /// Percentage of touches within 1 pixel of ground truth
    var accuracy1Pixel: Double {
        guard !positionErrors.isEmpty else { return 0 }
        let withinThreshold = positionErrors.filter { $0 <= 1.0 }.count
        return Double(withinThreshold) / Double(positionErrors.count) * 100
    }

    /// Percentage of touches within 3 pixels of ground truth
    var accuracy3Pixels: Double {
        guard !positionErrors.isEmpty else { return 0 }
        let withinThreshold = positionErrors.filter { $0 <= 3.0 }.count
        return Double(withinThreshold) / Double(positionErrors.count) * 100
    }

    /// Summary description
    var summary: String {
        """
        Positional Accuracy Metrics
        ─────────────────────────
        Mean Absolute Error: \(String(format: "%.2f", meanAbsoluteError)) pixels
        Std Deviation:       \(String(format: "%.2f", standardDeviation)) pixels
        Min Error:           \(String(format: "%.2f", minError)) pixels
        Max Error:           \(String(format: "%.2f", maxError)) pixels
        Within 1px:          \(String(format: "%.2f%%", accuracy1Pixel))
        Within 3px:          \(String(format: "%.2f%%", accuracy3Pixels))
        Total Samples:       \(positionErrors.count)
        """
    }
}

// MARK: - Benchmark Results

/// Complete benchmark results for a test run
struct BenchmarkResults {
    /// Unique identifier for this run
    let runId: String

    /// When the benchmark was run
    let timestamp: Date

    /// Dataset used
    let dataset: TestDataset

    /// Overall accuracy metrics
    let accuracyMetrics: AccuracyMetrics

    /// Positional accuracy metrics
    let positionalMetrics: PositionalAccuracyMetrics

    /// Average processing time per frame (milliseconds)
    let averageLatency: Double

    /// Average frame rate achieved
    let averageFPS: Double

    /// Peak memory usage (megabytes)
    let peakMemoryMB: Double

    /// JSON representation for export
    var jsonRepresentation: [String: Any] {
        [
            "run_id": runId,
            "timestamp": ISO8601DateFormatter().string(from: timestamp),
            "dataset_id": dataset.datasetId,
            "device": dataset.deviceModel,
            "ios_version": dataset.iosVersion,
            "accuracy_metrics": [
                "precision": accuracyMetrics.precision,
                "recall": accuracyMetrics.recall,
                "f1_score": accuracyMetrics.f1Score,
                "accuracy": accuracyMetrics.accuracy,
                "false_positive_rate": accuracyMetrics.falsePositiveRate,
                "false_negative_rate": accuracyMetrics.falseNegativeRate,
            ],
            "positional_metrics": [
                "mean_absolute_error": positionalMetrics.meanAbsoluteError,
                "std_deviation": positionalMetrics.standardDeviation,
                "max_error": positionalMetrics.maxError,
                "accuracy_1px": positionalMetrics.accuracy1Pixel,
                "accuracy_3px": positionalMetrics.accuracy3Pixels,
            ],
            "performance": [
                "average_latency_ms": averageLatency,
                "average_fps": averageFPS,
                "peak_memory_mb": peakMemoryMB,
            ],
        ]
    }

    /// Formatted summary for console output
    var summary: String {
        """
        ═══════════════════════════════════════════════════════
        BENCHMARK RESULTS: \(runId)
        ═══════════════════════════════════════════════════════

        Dataset Information
        ───────────────────────────────────────────────────────
        \(dataset.description)

        \(accuracyMetrics.summary)

        \(positionalMetrics.summary)

        Performance Metrics
        ───────────────────────────────────────────────────────
        Average Latency:     \(String(format: "%.2f", averageLatency)) ms
        Average FPS:         \(String(format: "%.1f", averageFPS))
        Peak Memory:         \(String(format: "%.1f", peakMemoryMB)) MB

        ═══════════════════════════════════════════════════════
        """
    }
}

// MARK: - Benchmark Runner

/// Benchmarking framework for evaluating vision pipeline accuracy
class BenchmarkRunner {
    /// Create ground truth dataset for testing
    static func createTestDataset(
        datasetId: String,
        deviceModel: String,
        iosVersion: String,
        annotations: [TouchAnnotation]
    ) -> TestDataset {
        TestDataset(
            datasetId: datasetId,
            deviceModel: deviceModel,
            iosVersion: iosVersion,
            annotations: annotations
        )
    }

    /// Evaluate accuracy metrics
    static func evaluateAccuracy(
        groundTruth: [TouchAnnotation],
        predictions: [TouchValidationResult]
    ) -> AccuracyMetrics {
        guard groundTruth.count == predictions.count else {
            fatalError("Ground truth and predictions must have same count")
        }

        var tp = 0, fp = 0, fn = 0, tn = 0

        for (truth, prediction) in zip(groundTruth, predictions) {
            let isExpectedTouch = case truth.expectedResult {
                case .touchValid:
                    true
                default:
                    false
            }

            let isPredictedTouch = case prediction {
                case .touchValid:
                    true
                default:
                    false
            }

            if isExpectedTouch && isPredictedTouch {
                tp += 1
            } else if !isExpectedTouch && isPredictedTouch {
                fp += 1
            } else if isExpectedTouch && !isPredictedTouch {
                fn += 1
            } else {
                tn += 1
            }
        }

        return AccuracyMetrics(
            truePositives: tp,
            falsePositives: fp,
            falseNegatives: fn,
            trueNegatives: tn
        )
    }

    /// Evaluate positional accuracy
    static func evaluatePositionalAccuracy(
        groundTruth: [(x: Float, y: Float)],
        predictions: [(x: Float, y: Float)]
    ) -> PositionalAccuracyMetrics {
        guard groundTruth.count == predictions.count else {
            fatalError("Ground truth and predictions must have same count")
        }

        let errors = zip(groundTruth, predictions).map { truth, prediction in
            let dx = truth.x - prediction.x
            let dy = truth.y - prediction.y
            return sqrt(dx * dx + dy * dy)
        }

        return PositionalAccuracyMetrics(positionErrors: errors)
    }

    /// Run full benchmark suite
    static func runBenchmark(
        dataset: TestDataset,
        visionPipeline: VisionPipelineManager,
        latencyMs: Double,
        fps: Double,
        memoryMB: Double
    ) -> BenchmarkResults {
        // In real scenario, process dataset frames and collect predictions
        let mockPredictions: [TouchValidationResult] = []

        let accuracyMetrics = evaluateAccuracy(
            groundTruth: dataset.annotations,
            predictions: mockPredictions
        )

        let positionalMetrics = evaluatePositionalAccuracy(
            groundTruth: dataset.annotations.map { ($0.groundTruthX, $0.groundTruthY) },
            predictions: [] // Would come from actual processing
        )

        return BenchmarkResults(
            runId: "bench_\(UUID().uuidString.prefix(8))",
            timestamp: Date(),
            dataset: dataset,
            accuracyMetrics: accuracyMetrics,
            positionalMetrics: positionalMetrics,
            averageLatency: latencyMs,
            averageFPS: fps,
            peakMemoryMB: memoryMB
        )
    }

    /// Export results to JSON
    static func exportResults(_ results: BenchmarkResults, to filePath: String) throws {
        let jsonData = try JSONSerialization.data(
            withJSONObject: results.jsonRepresentation,
            options: .prettyPrinted
        )
        try jsonData.write(to: URL(fileURLWithPath: filePath))
    }

    /// Export results to CSV
    static func exportResultsCSV(_ results: BenchmarkResults, to filePath: String) throws {
        let csv = """
        Metric,Value
        Run ID,\(results.runId)
        Timestamp,\(ISO8601DateFormatter().string(from: results.timestamp))
        Dataset,\(results.dataset.datasetId)
        Device,\(results.dataset.deviceModel)
        iOS Version,\(results.dataset.iosVersion)
        Precision,\(String(format: "%.4f", results.accuracyMetrics.precision))
        Recall,\(String(format: "%.4f", results.accuracyMetrics.recall))
        F1 Score,\(String(format: "%.4f", results.accuracyMetrics.f1Score))
        Accuracy,\(String(format: "%.4f", results.accuracyMetrics.accuracy))
        False Positive Rate,\(String(format: "%.4f", results.accuracyMetrics.falsePositiveRate))
        False Negative Rate,\(String(format: "%.4f", results.accuracyMetrics.falseNegativeRate))
        Mean Absolute Error,\(String(format: "%.2f", results.positionalMetrics.meanAbsoluteError))
        Standard Deviation,\(String(format: "%.2f", results.positionalMetrics.standardDeviation))
        Accuracy 1px,\(String(format: "%.2f", results.positionalMetrics.accuracy1Pixel))
        Accuracy 3px,\(String(format: "%.2f", results.positionalMetrics.accuracy3Pixels))
        Average Latency (ms),\(String(format: "%.2f", results.averageLatency))
        Average FPS,\(String(format: "%.1f", results.averageFPS))
        Peak Memory (MB),\(String(format: "%.1f", results.peakMemoryMB))
        """

        try csv.write(toFile: filePath, atomically: true, encoding: .utf8)
    }
}

// MARK: - Extensions for switch case pattern matching

extension TouchValidationResult {
    var caseValue: String {
        switch self {
        case .touchValid:
            return "touchValid"
        case .hoverState:
            return "hoverState"
        case .outsideKey:
            return "outsideKey"
        case .shadowMismatch:
            return "shadowMismatch"
        case .lowConfidence:
            return "lowConfidence"
        case .idle:
            return "idle"
        }
    }
}
