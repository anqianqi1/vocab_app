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