import SwiftUI
import VocabularyData

@main
struct VocabularyDemoApp: App {
    private let lessonRepository: StructuredLessonRepository
    private let wordRepository: WordRepository
    @State private var store = ProfileStore()

    init() {
        // Bundle.module is needed for SPM resource bundling; Bundle.main for .app bundles.
        let bundle: Bundle = Bundle.module.url(forResource: "grade-4_all_lessons_extraction", withExtension: "json") != nil
            ? .module : .main
        let databaseURL = bundle.url(forResource: "vocabulary", withExtension: "sqlite")
        self.lessonRepository = BundledLessonRepository(bundle: bundle)
        self.wordRepository = HybridWordRepository(bundle: bundle, databaseURL: databaseURL)
    }

    var body: some Scene {
        WindowGroup {
            if store.current == nil {
                ProfileGateView(store: store)
            } else {
                HomeView(store: store, lessonRepository: lessonRepository, wordRepository: wordRepository)
            }
        }
    }
}
