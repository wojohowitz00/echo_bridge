import Foundation
import CoreGraphics

/// Represents a single key on the virtual keyboard
struct KeyboardKey: Equatable, Hashable {
    /// Unique identifier for the key
    let identifier: String

    /// Display character(s) for the key
    let character: String

    /// Position and size in normalized coordinates (0.0 - 1.0)
    let frame: CGRect

    /// Row index in the keyboard layout
    let row: Int

    /// Column index in the keyboard layout
    let column: Int

    /// Shifted/uppercase variant of the character
    let shiftedCharacter: String?

    /// Alternative characters accessible via long press
    let alternateCharacters: [String]

    /// Key type (letter, number, space, etc.)
    let keyType: KeyType

    /// Whether the key is currently in a pressed/highlighted state
    var isPressed: Bool = false

    /// Number of times this key has been pressed
    var pressCount: Int = 0

    /// Last time this key was pressed
    var lastPressTime: Date?

    /// Hash support for use in Sets/Dicts
    func hash(into hasher: inout Hasher) {
        hasher.combine(identifier)
    }

    /// Get the character to input based on shift state
    func getCharacter(shifted: Bool) -> String {
        return shifted && shiftedCharacter != nil ? shiftedCharacter! : character
    }

    /// Check if a point (in normalized coordinates) is within this key
    func contains(point: CGPoint) -> Bool {
        return frame.contains(point)
    }

    /// Check if a point is within this key with optional margin
    func contains(point: CGPoint, margin: CGFloat) -> Bool {
        let expandedFrame = frame.insetBy(dx: -margin, dy: -margin)
        return expandedFrame.contains(point)
    }

    /// Distance from this key's center to a point
    func distance(to point: CGPoint) -> CGFloat {
        let center = CGPoint(x: frame.midX, y: frame.midY)
        return hypot(point.x - center.x, point.y - center.y)
    }
}

/// Enumeration of keyboard key types
enum KeyType: String, Equatable, Codable {
    case letter
    case number
    case punctuation
    case space
    case backspace
    case enter
    case shift
    case special
    case function

    /// Human-readable description
    var description: String {
        switch self {
        case .letter:
            return "Letter"
        case .number:
            return "Number"
        case .punctuation:
            return "Punctuation"
        case .space:
            return "Space"
        case .backspace:
            return "Backspace"
        case .enter:
            return "Enter"
        case .shift:
            return "Shift"
        case .special:
            return "Special"
        case .function:
            return "Function"
        }
    }
}

/// Keyboard layout definition
struct KeyboardLayout: Equatable {
    /// Name of the layout (e.g., "QWERTY")
    let name: String

    /// Language code for the layout (e.g., "en", "es")
    let languageCode: String

    /// All keys organized by row then column
    let rows: [[KeyboardKey]]

    /// Overall keyboard dimensions in normalized coordinates
    let frame: CGRect

    /// Spacing between keys (in normalized coordinates)
    let keySpacing: CGFloat

    /// Computed total number of keys
    var keyCount: Int {
        return rows.reduce(0) { $0 + $1.count }
    }

    /// Get all keys as a flat array
    var allKeys: [KeyboardKey] {
        return rows.flatMap { $0 }
    }

    /// Find a key by identifier
    func key(withIdentifier id: String) -> KeyboardKey? {
        return allKeys.first { $0.identifier == id }
    }

    /// Find a key containing a point in normalized coordinates
    func key(at point: CGPoint) -> KeyboardKey? {
        for row in rows {
            for key in row {
                if key.contains(point: point) {
                    return key
                }
            }
        }
        return nil
    }

    /// Find the nearest key to a point
    func nearestKey(to point: CGPoint) -> KeyboardKey? {
        let distances = allKeys.map { key -> (key: KeyboardKey, distance: CGFloat) in
            return (key, key.distance(to: point))
        }

        return distances.min(by: { $0.distance < $1.distance })?.key
    }
}

/// Standard QWERTY keyboard layout builder
struct QWERTYLayoutBuilder {
    static func buildLayout(
        languageCode: String = "en",
        keyboardFrame: CGRect = CGRect(x: 0.05, y: 0.5, width: 0.9, height: 0.4),
        keySpacing: CGFloat = 0.01
    ) -> KeyboardLayout {
        // Define key strings for each row
        let numberRow = "1234567890"
        let firstRow = "qwertyuiop"
        let secondRow = "asdfghjkl"
        let thirdRow = "zxcvbnm"

        // Calculate key dimensions
        let cols = 10  // Maximum columns (number row)
        let rows = 4   // 4 rows total

        let availableWidth = keyboardFrame.width - (keySpacing * CGFloat(cols - 1))
        let availableHeight = keyboardFrame.height - (keySpacing * CGFloat(rows - 1))

        let keyWidth = availableWidth / CGFloat(cols)
        let keyHeight = availableHeight / CGFloat(rows)

        var keyboardRows: [[KeyboardKey]] = []

        // Number row
        var row: [KeyboardKey] = []
        for (index, char) in numberRow.enumerated() {
            let x = keyboardFrame.origin.x + CGFloat(index) * (keyWidth + keySpacing)
            let y = keyboardFrame.origin.y
            let keyFrame = CGRect(x: x, y: y, width: keyWidth, height: keyHeight)

            let key = KeyboardKey(
                identifier: "key_\(index)",
                character: String(char),
                frame: keyFrame,
                row: 0,
                column: index,
                shiftedCharacter: nil,  // Numbers don't shift
                alternateCharacters: [],
                keyType: .number
            )
            row.append(key)
        }
        keyboardRows.append(row)

        // QWERTY row
        row = []
        for (index, char) in firstRow.enumerated() {
            let x = keyboardFrame.origin.x + CGFloat(index) * (keyWidth + keySpacing)
            let y = keyboardFrame.origin.y + (keyHeight + keySpacing)
            let keyFrame = CGRect(x: x, y: y, width: keyWidth, height: keyHeight)

            let key = KeyboardKey(
                identifier: "key_\(char)",
                character: String(char),
                frame: keyFrame,
                row: 1,
                column: index,
                shiftedCharacter: String(char).uppercased(),
                alternateCharacters: [],
                keyType: .letter
            )
            row.append(key)
        }
        keyboardRows.append(row)

        // ASDF row
        row = []
        for (index, char) in secondRow.enumerated() {
            let x = keyboardFrame.origin.x + CGFloat(index) * (keyWidth + keySpacing)
            let y = keyboardFrame.origin.y + 2 * (keyHeight + keySpacing)
            let keyFrame = CGRect(x: x, y: y, width: keyWidth, height: keyHeight)

            let key = KeyboardKey(
                identifier: "key_\(char)",
                character: String(char),
                frame: keyFrame,
                row: 2,
                column: index,
                shiftedCharacter: String(char).uppercased(),
                alternateCharacters: [],
                keyType: .letter
            )
            row.append(key)
        }
        keyboardRows.append(row)

        // ZXCV row
        row = []
        for (index, char) in thirdRow.enumerated() {
            let x = keyboardFrame.origin.x + CGFloat(index) * (keyWidth + keySpacing)
            let y = keyboardFrame.origin.y + 3 * (keyHeight + keySpacing)
            let keyFrame = CGRect(x: x, y: y, width: keyWidth, height: keyHeight)

            let key = KeyboardKey(
                identifier: "key_\(char)",
                character: String(char),
                frame: keyFrame,
                row: 3,
                column: index,
                shiftedCharacter: String(char).uppercased(),
                alternateCharacters: [],
                keyType: .letter
            )
            row.append(key)
        }
        keyboardRows.append(row)

        return KeyboardLayout(
            name: "QWERTY",
            languageCode: languageCode,
            rows: keyboardRows,
            frame: keyboardFrame,
            keySpacing: keySpacing
        )
    }
}
