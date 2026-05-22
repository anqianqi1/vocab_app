import SwiftUI
import VocabularyContent
import VocabularyData

struct ContentView: View {
    @State private var lessons: [StructuredLesson] = []
    @State private var isLoading = true
    @State private var error: Error?

    private let repository: StructuredLessonRepository

    init(repository: StructuredLessonRepository) {
        self.repository = repository
    }

    var body: some View {
        NavigationStack {
            Group {
                if isLoading && lessons.isEmpty {
                    ProgressView("Loading lessons…")
                } else if let error {
                    VStack(spacing: 12) {
                        Text("Unable to load lessons")
                            .font(.headline)
                        Text(error.localizedDescription)
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                            .multilineTextAlignment(.center)
                        Button("Retry") { loadLessons() }
                            .buttonStyle(.borderedProminent)
                    }
                    .padding()
                } else {
                    lessonList
                }
            }
            .navigationTitle("Vocabulary")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Refresh") { loadLessons() }
                }
            }
            .task { loadLessons() }
            .navigationDestination(for: StructuredLesson.self) { lesson in
                LessonDetailView(lesson: lesson)
            }
        }
    }

    // MARK: - Lesson List

    private var lessonList: some View {
        List(lessons) { lesson in
            NavigationLink(value: lesson) {
                lessonRow(lesson)
            }
        }
        .listStyle(.insetGrouped)
    }

    private func lessonRow(_ lesson: StructuredLesson) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            // Lesson number & title
            HStack {
                Text("Lesson \(lesson.lessonNumber)")
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.white)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)
                    .background(
                        RoundedRectangle(cornerRadius: 6)
                            .fill(Color.accentColor)
                    )

                Text(lesson.title)
                    .font(.headline)
            }

            // Roots
            if !lesson.roots.isEmpty {
                HStack(spacing: 6) {
                    ForEach(lesson.roots, id: \.root) { root in
                        Text(root.root)
                            .font(.caption.weight(.medium))
                            .foregroundStyle(.purple)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 2)
                            .background(
                                RoundedRectangle(cornerRadius: 4)
                                    .fill(.purple.opacity(0.1))
                            )
                    }
                }
            }

            // Word counts by group
            HStack(spacing: 12) {
                wordCountBadge(label: "Key", count: lesson.keyWords.count, color: .green)
                wordCountBadge(label: "Familiar", count: lesson.familiarWords.count, color: .blue)
                wordCountBadge(label: "Challenge", count: lesson.challengeWords.count, color: .orange)
            }
        }
        .padding(.vertical, 4)
    }

    private func wordCountBadge(label: String, count: Int, color: Color) -> some View {
        HStack(spacing: 4) {
            Circle()
                .fill(color)
                .frame(width: 8, height: 8)
            Text("\(count) \(label)")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }

    // MARK: - Data Loading

    private func loadLessons() {
        Task {
            do {
                isLoading = true
                error = nil
                lessons = try await repository.loadLessons()
            } catch {
                self.error = error
            }
            isLoading = false
        }
    }
}
