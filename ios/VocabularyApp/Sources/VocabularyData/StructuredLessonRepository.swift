import Foundation
import VocabularyContent

/// Repository that loads structured lesson data from bundled JSON files.
public protocol StructuredLessonRepository {
    func loadLessons(for grade: Grade) async throws -> [StructuredLesson]
    func lesson(withNumber number: Int, grade: Grade) async throws -> StructuredLesson?
}

public final class BundledLessonRepository: StructuredLessonRepository {
    private let bundle: Bundle

    public init(bundle: Bundle = .main) {
        self.bundle = bundle
    }

    /// Returns the JSON file name for a given grade.
    private func fileName(for grade: Grade) -> String {
        "grade-\(grade.level)_all_lessons_extraction"
    }

    public func loadLessons(for grade: Grade) async throws -> [StructuredLesson] {
        let name = fileName(for: grade)
        guard let url = bundle.url(forResource: name, withExtension: "json") else {
            throw RepositoryError.fileNotFound(name)
        }
        let data = try Data(contentsOf: url)
        let decoder = JSONDecoder()
        return try decoder.decode([StructuredLesson].self, from: data)
    }

    public func lesson(withNumber number: Int, grade: Grade) async throws -> StructuredLesson? {
        let lessons = try await loadLessons(for: grade)
        return lessons.first { $0.lessonNumber == number }
    }
}

public enum RepositoryError: LocalizedError {
    case fileNotFound(String)

    public var errorDescription: String? {
        switch self {
        case .fileNotFound(let name):
            return "Could not find bundled file: \(name).json"
        }
    }
}

// MARK: - Word Repository

/// Repository that loads word-centric data from bundled words.json files.
public protocol WordRepository {
    func loadWords(for grade: Grade) async throws -> [WordEntry]
    func words(forLesson lessonNumber: Int, grade: Grade) async throws -> [WordEntry]
    func words(forGroup group: WordGroup, grade: Grade) async throws -> [WordEntry]
    func words(forRoot root: String, grade: Grade) async throws -> [WordEntry]
}

public final class BundledWordRepository: WordRepository {
    private let bundle: Bundle

    public init(bundle: Bundle = .main) {
        self.bundle = bundle
    }

    /// Returns the JSON file name for a given grade's word-centric data.
    private func fileName(for grade: Grade) -> String {
        "grade-\(grade.level)_words"
    }

    public func loadWords(for grade: Grade) async throws -> [WordEntry] {
        let name = fileName(for: grade)
        guard let url = bundle.url(forResource: name, withExtension: "json") else {
            throw RepositoryError.fileNotFound(name)
        }
        let data = try Data(contentsOf: url)
        let decoder = JSONDecoder()
        return try decoder.decode([WordEntry].self, from: data)
    }

    public func words(forLesson lessonNumber: Int, grade: Grade) async throws -> [WordEntry] {
        let all = try await loadWords(for: grade)
        return all.filter { $0.lessonNumber == lessonNumber }
    }

    public func words(forGroup group: WordGroup, grade: Grade) async throws -> [WordEntry] {
        let all = try await loadWords(for: grade)
        return all.filter { $0.group == group }
    }

    public func words(forRoot root: String, grade: Grade) async throws -> [WordEntry] {
        let all = try await loadWords(for: grade)
        return all.filter { $0.root == root }
    }
}