import Foundation
import VocabularyContent

/// Repository that loads structured lesson data from the bundled JSON file.
public protocol StructuredLessonRepository {
    func loadLessons() async throws -> [StructuredLesson]
    func lesson(withNumber number: Int) async throws -> StructuredLesson?
}

public final class BundledLessonRepository: StructuredLessonRepository {
    private let jsonFileName: String
    private let bundle: Bundle

    public init(jsonFileName: String = "all_lessons_extraction", bundle: Bundle = .main) {
        self.jsonFileName = jsonFileName
        self.bundle = bundle
    }

    public func loadLessons() async throws -> [StructuredLesson] {
        guard let url = bundle.url(forResource: jsonFileName, withExtension: "json") else {
            throw RepositoryError.fileNotFound(jsonFileName)
        }
        let data = try Data(contentsOf: url)
        let decoder = JSONDecoder()
        return try decoder.decode([StructuredLesson].self, from: data)
    }

    public func lesson(withNumber number: Int) async throws -> StructuredLesson? {
        let lessons = try await loadLessons()
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