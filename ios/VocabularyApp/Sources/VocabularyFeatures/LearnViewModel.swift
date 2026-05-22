import Foundation
import Observation
import VocabularyContent

@MainActor
@Observable
public final class LearnViewModel {
    public let lesson: StructuredLesson
    public private(set) var selectedGroup: WordGroup?
    public private(set) var currentIndex: Int = 0
    public private(set) var showDefinition: Bool = false

    /// Words filtered by the currently selected group (nil = all).
    public var filteredWords: [WordDetail] {
        if let group = selectedGroup {
            return lesson.words(in: group)
        }
        return lesson.wordDetails
    }

    public var currentWord: WordDetail? {
        guard currentIndex < filteredWords.count else { return nil }
        return filteredWords[currentIndex]
    }

    public var progress: String {
        guard !filteredWords.isEmpty else { return "0 of 0" }
        return "\(currentIndex + 1) of \(filteredWords.count)"
    }

    public var progressFraction: Double {
        guard !filteredWords.isEmpty else { return 0 }
        return Double(currentIndex + 1) / Double(filteredWords.count)
    }

    public var hasNext: Bool {
        currentIndex + 1 < filteredWords.count
    }

    public var hasPrevious: Bool {
        currentIndex > 0
    }

    public init(lesson: StructuredLesson) {
        self.lesson = lesson
    }

    public func selectGroup(_ group: WordGroup?) {
        selectedGroup = group
        currentIndex = 0
        showDefinition = false
    }

    public func toggleDefinition() {
        withAnimation {
            showDefinition.toggle()
        }
    }

    public func nextWord() {
        guard hasNext else { return }
        currentIndex += 1
        showDefinition = false
    }

    public func previousWord() {
        guard hasPrevious else { return }
        currentIndex -= 1
        showDefinition = false
    }

    public func reset() {
        currentIndex = 0
        showDefinition = false
    }
}

/// Helper to wrap animation calls (since @Observable doesn't use withAnimation directly).
private func withAnimation(_ body: () -> Void) {
    body()
}