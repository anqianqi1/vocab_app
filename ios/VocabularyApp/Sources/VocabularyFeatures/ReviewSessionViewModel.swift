import Foundation
import Observation
import VocabularyContent

@MainActor
@Observable
public final class ReviewSessionViewModel {
    private(set) var cards: [ReviewCard]
    private(set) var entriesByID: [String: VocabularyEntry]

    public private(set) var currentIndex: Int = 0
    public private(set) var showDefinition: Bool = false
    public private(set) var completedCards: [ReviewCard] = []
    public private(set) var masteredCards: [ReviewCard] = []
    public private(set) var needsPracticeCards: [ReviewCard] = []

    public var currentCard: ReviewCard? {
        guard currentIndex < cards.count else { return nil }
        return cards[currentIndex]
    }

    public var currentEntry: VocabularyEntry? {
        guard let entryID = currentCard?.entryID else { return nil }
        return entriesByID[entryID]
    }

    public init(entries: [VocabularyEntry]) {
        self.entriesByID = Dictionary(uniqueKeysWithValues: entries.map { ($0.id, $0) })
        self.cards = entries.map { entry in
            ReviewCard(id: entry.id, entryID: entry.id, prompt: .flashcard)
        }
    }

    public func toggleCard() {
        showDefinition.toggle()
    }

    public func markKnown() {
        advance(mastered: true)
    }

    public func markNeedsPractice() {
        advance(mastered: false)
    }

    private func advance(mastered: Bool) {
        guard let card = currentCard else { return }
        completedCards.append(card)
        if mastered {
            masteredCards.append(card)
        } else {
            needsPracticeCards.append(card)
        }
        showDefinition = false
        if currentIndex + 1 < cards.count {
            currentIndex += 1
        } else {
            currentIndex = cards.count
        }
    }

    public func reset() {
        currentIndex = 0
        showDefinition = false
        completedCards.removeAll()
        masteredCards.removeAll()
        needsPracticeCards.removeAll()
    }
}
