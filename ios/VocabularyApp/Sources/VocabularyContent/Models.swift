import Foundation

public struct Lesson: Identifiable, Hashable, Codable {
    public let id: String
    public let title: String
    public let section: String
    public let sourceID: String
    public let entryCount: Int

    public init(id: String, title: String, section: String, sourceID: String, entryCount: Int) {
        self.id = id
        self.title = title
        self.section = section
        self.sourceID = sourceID
        self.entryCount = entryCount
    }
}

public struct VocabularyEntry: Identifiable, Hashable, Codable {
    public let id: String
    public let term: String
    public let definition: String
    public let partOfSpeech: String?
    public let example: String?
    public let section: String?
    public let category: String
    public let sourceID: String
    public let relatedTerms: [String]
    public let warnings: [String]

    public init(
        id: String,
        term: String,
        definition: String,
        partOfSpeech: String?,
        example: String?,
        section: String?,
        category: String,
        sourceID: String,
        relatedTerms: [String],
        warnings: [String]
    ) {
        self.id = id
        self.term = term
        self.definition = definition
        self.partOfSpeech = partOfSpeech
        self.example = example
        self.section = section
        self.category = category
        self.sourceID = sourceID
        self.relatedTerms = relatedTerms
        self.warnings = warnings
    }
}

public enum ReviewPrompt: Equatable, Hashable, Codable {
    case flashcard
    case multipleChoice(options: [String])
    case fillInBlank
}

public struct ReviewCard: Identifiable, Hashable, Codable {
    public let id: String
    public let entryID: String
    public let prompt: ReviewPrompt

    public init(id: String, entryID: String, prompt: ReviewPrompt) {
        self.id = id
        self.entryID = entryID
        self.prompt = prompt
    }
}
