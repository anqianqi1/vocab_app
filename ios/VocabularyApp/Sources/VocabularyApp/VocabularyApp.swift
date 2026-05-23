import SwiftUI
import VocabularyData

@main
struct VocabularyDemoApp: App {
    private let lessonRepository: StructuredLessonRepository

    init() {
        // Bundle.module is needed for SPM resource bundling; Bundle.main for .app bundles.
        let bundle: Bundle = Bundle.module.url(forResource: "grade-4_all_lessons_extraction", withExtension: "json") != nil
            ? .module : .main
        self.lessonRepository = BundledLessonRepository(bundle: bundle)
    }

    var body: some Scene {
        WindowGroup {
            ContentView(repository: lessonRepository)
        }
    }
}
