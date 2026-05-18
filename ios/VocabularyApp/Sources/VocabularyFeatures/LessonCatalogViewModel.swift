import Foundation
import Observation
import VocabularyContent
import VocabularyData

@MainActor
@Observable
public final class LessonCatalogViewModel {
    private let lessonRepository: LessonRepository

    public private(set) var lessons: [Lesson] = []
    public private(set) var isLoading = false
    public private(set) var error: Error?

    public init(lessonRepository: LessonRepository) {
        self.lessonRepository = lessonRepository
    }

    public func load() {
        Task {
            do {
                isLoading = true
                error = nil
                lessons = try await lessonRepository.lessons()
            } catch {
                self.error = error
            }
            isLoading = false
        }
    }
}
