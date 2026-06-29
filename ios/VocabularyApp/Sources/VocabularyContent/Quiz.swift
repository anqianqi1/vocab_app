import Foundation

/// A single quiz question generated from word data.
public struct ExamQuestion: Identifiable, Hashable {
    public enum Kind: String, Hashable {
        case pictureToWord     // show image, choose the word
        case definitionToWord  // show definition, choose the word
        case wordToDefinition  // show word, choose the definition
        case typeTheWord       // show definition, type the word
    }

    public let id: UUID
    public let kind: Kind
    public let prompt: String          // definition text, or the word
    public let imageName: String?      // for pictureToWord
    public let answer: String
    public let options: [String]

    public init(
        id: UUID = UUID(),
        kind: Kind,
        prompt: String,
        imageName: String?,
        answer: String,
        options: [String]
    ) {
        self.id = id
        self.kind = kind
        self.prompt = prompt
        self.imageName = imageName
        self.answer = answer
        self.options = options
    }
}

/// Result of one completed weekly exam.
public struct ExamResult: Hashable {
    public let correct: Int
    public let total: Int
    public let xpEarned: Int

    public init(correct: Int, total: Int, xpEarned: Int) {
        self.correct = correct
        self.total = total
        self.xpEarned = xpEarned
    }

    public var percent: Int { total == 0 ? 0 : Int((Double(correct) / Double(total)) * 100) }
    public var passed: Bool { percent >= 70 }
}
