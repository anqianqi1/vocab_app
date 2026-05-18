import SwiftUI
import VocabularyContent
import VocabularyFeatures
import VocabularyData

struct ContentView: View {
    @State private var viewModel: LessonCatalogViewModel
    private let entryRepository: EntryRepository

    init(lessonRepository: LessonRepository, entryRepository: EntryRepository) {
        _viewModel = State(initialValue: LessonCatalogViewModel(lessonRepository: lessonRepository))
        self.entryRepository = entryRepository
    }

    var body: some View {
        NavigationStack {
            Group {
                if viewModel.isLoading && viewModel.lessons.isEmpty {
                    ProgressView("Loading lessons…")
                } else {
                    List(viewModel.lessons) { lesson in
                        NavigationLink(value: lesson) {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(lesson.title)
                                    .font(.headline)
                                Text("\(lesson.entryCount) entries")
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                }
            }
            .navigationTitle("Lessons")
            .toolbar {
                #if os(iOS)
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Refresh") { viewModel.load() }
                }
                #else
                ToolbarItem {
                    Button("Refresh") { viewModel.load() }
                }
                #endif
            }
            .task { viewModel.load() }
            .navigationDestination(for: Lesson.self) { lesson in
                ReviewSessionLoader(lesson: lesson, entryRepository: entryRepository)
            }
        }
    }
}
