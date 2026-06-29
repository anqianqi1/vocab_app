import Foundation
import Observation
import VocabularyContent

@MainActor
@Observable
public final class ExamViewModel {
    public let questions: [ExamQuestion]
    public private(set) var index: Int = 0
    public private(set) var correct: Int = 0
    public private(set) var selected: String?
    public private(set) var isFinished: Bool = false

    private let xpPerCorrect = 10

    public init(questions: [ExamQuestion]) {
        self.questions = questions
    }

    public var current: ExamQuestion? {
        index < questions.count ? questions[index] : nil
    }

    public var progress: Double {
        questions.isEmpty ? 0 : Double(index) / Double(questions.count)
    }

    public var hasAnswered: Bool { selected != nil }

    public func choose(_ option: String) {
        guard selected == nil else { return }
        selected = option
        if option.caseInsensitiveCompare(current?.answer ?? "") == .orderedSame { correct += 1 }
    }

    public func isCorrect(_ option: String) -> Bool {
        option.caseInsensitiveCompare(current?.answer ?? "") == .orderedSame
    }

    public func advance() {
        guard selected != nil else { return }
        if index + 1 < questions.count {
            index += 1
            selected = nil
        } else {
            isFinished = true
        }
    }

    public var result: ExamResult {
        ExamResult(correct: correct, total: questions.count, xpEarned: correct * xpPerCorrect)
    }
}
