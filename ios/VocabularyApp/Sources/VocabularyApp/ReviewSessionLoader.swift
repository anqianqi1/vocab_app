import SwiftUI
import VocabularyContent
import VocabularyData
import VocabularyFeatures

struct ReviewSessionLoader: View {
    let lesson: Lesson
    let entryRepository: EntryRepository

    @State private var entries: [VocabularyEntry] = []
    @State private var isLoading = true
    @State private var error: Error?

    var body: some View {
        Group {
            if let error {
                VStack(spacing: 12) {
                    Text("Unable to load lesson")
                        .font(.headline)
                    Text(error.localizedDescription)
                        .multilineTextAlignment(.center)
                        .font(.subheadline)
                    Button("Retry") { load() }
                }
                .padding()
            } else if isLoading {
                ProgressView("Loading entries…")
            } else {
                ReviewSessionView(
                    viewModel: ReviewSessionViewModel(entries: entries),
                    lesson: lesson
                )
            }
        }
        .navigationTitle(lesson.title)
        .task { load() }
    }

    private func load() {
        Task {
            do {
                isLoading = true
                error = nil
                entries = try await entryRepository.entries(forLesson: lesson.id)
            } catch {
                self.error = error
            }
            isLoading = false
        }
    }
}
