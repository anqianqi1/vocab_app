import Foundation
import Observation
import VocabularyContent

@MainActor
@Observable
public final class CompletionSummaryViewModel {
    public let lesson: Lesson
    public let totalCards: Int
    public let masteredCount: Int
    public let needsPracticeCount: Int

    public var accuracy: Double {
        guard totalCards > 0 else { return 0 }
        return Double(masteredCount) / Double(totalCards)
    }

    public init(lesson: Lesson, mastered: Int, needsPractice: Int) {
        self.lesson = lesson
        self.masteredCount = mastered
        self.needsPracticeCount = needsPractice
        self.totalCards = mastered + needsPractice
    }
}
