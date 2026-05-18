import SwiftUI
import VocabularyData

@main
struct VocabularyDemoApp: App {
    private let dataStore: SQLiteDataStore

    init() {
        self.dataStore = VocabularyDemoApp.makeDataStore()
    }

    var body: some Scene {
        WindowGroup {
            ContentView(lessonRepository: dataStore, entryRepository: dataStore)
        }
    }

    private static func makeDataStore() -> SQLiteDataStore {
        guard let url = VocabularyDemoApp.resolveDatabaseURL() else {
            fatalError("Missing bundled vocabulary.sqlite – see docs/app/APP_PLAN.md")
        }
        do {
            return try SQLiteDataStore(databaseURL: url)
        } catch {
            fatalError("Failed to open vocabulary.sqlite: \(error)")
        }
    }

    private static func resolveDatabaseURL() -> URL? {
        if let mainURL = Bundle.main.url(forResource: "vocabulary", withExtension: "sqlite") {
            return mainURL
        }
        return Bundle.module.url(forResource: "vocabulary", withExtension: "sqlite")
    }
}
