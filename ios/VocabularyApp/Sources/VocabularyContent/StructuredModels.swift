import Foundation

/// Represents a grade level with its associated lessons.
public struct Grade: Identifiable, Hashable {
    public var id: Int { level }
    public let level: Int
    public let displayName: String

    public init(level: Int) {
        self.level = level
        self.displayName = "Grade \(level)"
    }

    public static let supportedGrades: [Grade] = [4, 5, 8, 10, 11].map(Grade.init)
}

/// A single word with its definition, part of speech, example, and group classification.
public struct WordDetail: Identifiable, Hashable, Codable {
    public var id: String { word }
    public let word: String
    public let group: WordGroup
    public let partOfSpeech: String
    public let definition: String
    public let example: String
    public let imageName: String?

    public init(word: String, group: WordGroup, partOfSpeech: String, definition: String, example: String, imageName: String? = nil) {
        self.word = word
        self.group = group
        self.partOfSpeech = partOfSpeech
        self.definition = definition
        self.example = example
        self.imageName = imageName
    }

    // MARK: Codable

    private enum CodingKeys: String, CodingKey {
        case word, group, senses, image
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        word = try container.decode(String.self, forKey: .word)
        group = try container.decode(WordGroup.self, forKey: .group)
        imageName = try container.decodeIfPresent(String.self, forKey: .image)

        var sensesContainer = try container.nestedUnkeyedContainer(forKey: .senses)
        if let firstSense = try? sensesContainer.decode(Sense.self) {
            partOfSpeech = firstSense.partOfSpeech
            definition = firstSense.definition
            example = firstSense.example
        } else {
            partOfSpeech = ""
            definition = ""
            example = ""
        }
    }

    public func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(word, forKey: .word)
        try container.encode(group, forKey: .group)
        try container.encodeIfPresent(imageName, forKey: .image)
        let sense = Sense(partOfSpeech: partOfSpeech, definition: definition, example: example)
        var sensesContainer = container.nestedUnkeyedContainer(forKey: .senses)
        try sensesContainer.encode(sense)
    }

    private struct Sense: Codable {
        let partOfSpeech: String
        let definition: String
        let example: String

        enum CodingKeys: String, CodingKey {
            case partOfSpeech = "part_of_speech"
            case definition, example
        }
    }
}

/// Classification of a word within a lesson.
public enum WordGroup: String, Hashable, Codable, CaseIterable {
    case key
    case familiar
    case challenge

    public var displayName: String {
        switch self {
        case .key: return "Key Words"
        case .familiar: return "Familiar Words"
        case .challenge: return "Challenge Words"
        }
    }

    public var icon: String {
        switch self {
        case .key: return "star.fill"
        case .familiar: return "book.fill"
        case .challenge: return "trophy.fill"
        }
    }
}

/// A Latin or Greek root taught in a lesson.
public struct LessonRoot: Hashable, Codable {
    public let root: String
    public let origin: String
    public let meaning: String
    public let exampleWord: String

    public init(root: String, origin: String, meaning: String, exampleWord: String) {
        self.root = root
        self.origin = origin
        self.meaning = meaning
        self.exampleWord = exampleWord
    }
}

/// A structured exercise from the textbook (synonyms, fill-in-blank, etc.).
public struct LessonExercise: Hashable, Codable {
    public let title: String
    public let lines: [String]

    public init(title: String, lines: [String]) {
        self.title = title
        self.lines = lines
    }
}

/// A complete lesson with roots, word groups, and exercises.
public struct StructuredLesson: Identifiable, Hashable, Codable {
    public var id: Int { lessonNumber }
    public let lessonNumber: Int
    public let title: String
    public let roots: [LessonRoot]
    public let keyWords: [String]
    public let familiarWords: [String]
    public let challengeWords: [String]
    public let wordDetails: [WordDetail]
    public let exercises: [LessonExercise]

    /// All word details filtered by group.
    public func words(in group: WordGroup) -> [WordDetail] {
        wordDetails.filter { $0.group == group }
    }

    /// Total number of word details across all groups.
    public var totalWordCount: Int {
        wordDetails.count
    }

    public init(
        lessonNumber: Int,
        title: String,
        roots: [LessonRoot],
        keyWords: [String],
        familiarWords: [String],
        challengeWords: [String],
        wordDetails: [WordDetail],
        exercises: [LessonExercise]
    ) {
        self.lessonNumber = lessonNumber
        self.title = title
        self.roots = roots
        self.keyWords = keyWords
        self.familiarWords = familiarWords
        self.challengeWords = challengeWords
        self.wordDetails = wordDetails
        self.exercises = exercises
    }
}

// MARK: - JSON Decoding Helpers

extension StructuredLesson {
    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        lessonNumber = try container.decode(Int.self, forKey: .lessonNumber)
        title = try container.decode(String.self, forKey: .title)
        roots = try container.decode([LessonRoot].self, forKey: .roots)
        keyWords = try container.decode([String].self, forKey: .keyWords)
        familiarWords = try container.decode([String].self, forKey: .familiarWords)
        challengeWords = try container.decode([String].self, forKey: .challengeWords)
        wordDetails = try container.decode([WordDetail].self, forKey: .wordDetails)
        exercises = (try? container.decode([LessonExercise].self, forKey: .exercises)) ?? []
    }

    private enum CodingKeys: String, CodingKey {
        case lessonNumber = "lesson_number"
        case title
        case roots
        case keyWords = "key_words"
        case familiarWords = "familiar_words"
        case challengeWords = "challenge_words"
        case wordDetails = "word_details"
        case exercises
    }
}

extension LessonRoot {
    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        root = try container.decode(String.self, forKey: .root)
        origin = try container.decode(String.self, forKey: .origin)
        meaning = try container.decode(String.self, forKey: .meaning)
        exampleWord = try container.decode(String.self, forKey: .exampleWord)
    }

    private enum CodingKeys: String, CodingKey {
        case root
        case origin
        case meaning
        case exampleWord = "example_word"
    }
}

// MARK: - Word-Centric Models

/// A self-contained word entry with all related info for flashcard-style learning.
public struct WordEntry: Identifiable, Hashable, Codable {
    public var id: String { word }
    public let word: String
    public let grade: Int
    public let lessonNumber: Int
    public let lessonTitle: String
    public let group: WordGroup
    public let root: String
    public let rootMeaning: String
    public let rootOrigin: String
    public let partOfSpeech: String
    public let definition: String
    public let example: String
    public let relatedWords: RelatedWords
    public let exercises: [LessonExercise]
    public let imageName: String?

    public init(
        word: String,
        grade: Int,
        lessonNumber: Int,
        lessonTitle: String,
        group: WordGroup,
        root: String,
        rootMeaning: String,
        rootOrigin: String,
        partOfSpeech: String,
        definition: String,
        example: String,
        relatedWords: RelatedWords,
        exercises: [LessonExercise],
        imageName: String? = nil
    ) {
        self.word = word
        self.grade = grade
        self.lessonNumber = lessonNumber
        self.lessonTitle = lessonTitle
        self.group = group
        self.root = root
        self.rootMeaning = rootMeaning
        self.rootOrigin = rootOrigin
        self.partOfSpeech = partOfSpeech
        self.definition = definition
        self.example = example
        self.relatedWords = relatedWords
        self.exercises = exercises
        self.imageName = imageName
    }

    // MARK: Codable

    private enum CodingKeys: String, CodingKey {
        case word, grade
        case lessonNumber = "lesson_number"
        case lessonTitle = "lesson_title"
        case group, root
        case rootMeaning = "root_meaning"
        case rootOrigin = "root_origin"
        case partOfSpeech = "part_of_speech"
        case definition, example
        case relatedWords = "related_words"
        case exercises
        case image
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        word = try container.decode(String.self, forKey: .word)
        grade = try container.decode(Int.self, forKey: .grade)
        lessonNumber = try container.decode(Int.self, forKey: .lessonNumber)
        lessonTitle = try container.decode(String.self, forKey: .lessonTitle)
        group = try container.decode(WordGroup.self, forKey: .group)
        root = try container.decode(String.self, forKey: .root)
        rootMeaning = try container.decode(String.self, forKey: .rootMeaning)
        rootOrigin = try container.decode(String.self, forKey: .rootOrigin)
        partOfSpeech = try container.decode(String.self, forKey: .partOfSpeech)
        definition = try container.decode(String.self, forKey: .definition)
        example = try container.decode(String.self, forKey: .example)
        relatedWords = try container.decode(RelatedWords.self, forKey: .relatedWords)
        exercises = (try? container.decode([LessonExercise].self, forKey: .exercises)) ?? []
        let decodedImage = try container.decodeIfPresent(String.self, forKey: .image)
        imageName = (decodedImage?.isEmpty == true) ? nil : decodedImage
    }

    public func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(word, forKey: .word)
        try container.encode(grade, forKey: .grade)
        try container.encode(lessonNumber, forKey: .lessonNumber)
        try container.encode(lessonTitle, forKey: .lessonTitle)
        try container.encode(group, forKey: .group)
        try container.encode(root, forKey: .root)
        try container.encode(rootMeaning, forKey: .rootMeaning)
        try container.encode(rootOrigin, forKey: .rootOrigin)
        try container.encode(partOfSpeech, forKey: .partOfSpeech)
        try container.encode(definition, forKey: .definition)
        try container.encode(example, forKey: .example)
        try container.encode(relatedWords, forKey: .relatedWords)
        try container.encode(exercises, forKey: .exercises)
        try container.encodeIfPresent(imageName, forKey: .image)
    }
}

/// Groups of related words for a word entry.
public struct RelatedWords: Hashable, Codable {
    public let sameRoot: [String]
    public let sameLesson: [String]

    public init(sameRoot: [String], sameLesson: [String]) {
        self.sameRoot = sameRoot
        self.sameLesson = sameLesson
    }

    private enum CodingKeys: String, CodingKey {
        case sameRoot = "same_root"
        case sameLesson = "same_lesson"
    }
}