import SwiftUI
import VocabularyContent
import VocabularyData

struct ContentView: View {
    @State private var selectedGrade: Grade?
    @State private var lessons: [StructuredLesson] = []
    @State private var isLoading = false
    @State private var error: Error?

    private let repository: StructuredLessonRepository

    init(repository: StructuredLessonRepository) {
        self.repository = repository
    }

    var body: some View {
        NavigationStack {
            Group {
                if selectedGrade == nil {
                    gradePickerView
                } else if isLoading && lessons.isEmpty {
                    ProgressView("Loading lessons…")
                } else if let error {
                    errorView(error)
                } else {
                    lessonListView
                }
            }
            .navigationTitle(selectedGrade.map { "Grade \($0.level)" } ?? "Vocabulary")
            .toolbar {
                if selectedGrade != nil {
                    ToolbarItem(placement: .navigationBarLeading) {
                        Button {
                            selectedGrade = nil
                            lessons = []
                        } label: {
                            HStack(spacing: 4) {
                                Image(systemName: "chevron.left")
                                Text("Grades")
                            }
                        }
                    }
                    ToolbarItem(placement: .navigationBarTrailing) {
                        Button("Refresh") { loadLessons() }
                    }
                }
            }
            .navigationDestination(for: StructuredLesson.self) { lesson in
                LessonDetailView(lesson: lesson)
            }
        }
    }

    // MARK: - Grade Picker

    private var gradePickerView: some View {
        VStack(spacing: 24) {
            Spacer()

            VStack(spacing: 8) {
                Image(systemName: "book.pages.fill")
                    .font(.system(size: 56))
                    .foregroundStyle(.blue)

                Text("Vocabulary Builder")
                    .font(.largeTitle.bold())

                Text("Choose your grade level to start learning")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }

            VStack(spacing: 12) {
                ForEach(Grade.supportedGrades) { grade in
                    Button {
                        selectGrade(grade)
                    } label: {
                        HStack {
                            Image(systemName: "\(grade.level).circle.fill")
                                .font(.title2)
                                .foregroundStyle(gradeColor(for: grade.level))
                            Text(grade.displayName)
                                .font(.title3.weight(.medium))
                                .foregroundStyle(.primary)
                            Spacer()
                            Image(systemName: "chevron.right")
                                .font(.subheadline.weight(.semibold))
                                .foregroundStyle(.secondary)
                        }
                        .padding(16)
                        .background(
                            RoundedRectangle(cornerRadius: 16)
                                .fill(Color(.systemBackground))
                                .shadow(color: .black.opacity(0.06), radius: 8, y: 2)
                        )
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal)

            Spacer()
        }
        .padding()
        .background(Color(.systemGroupedBackground))
    }

    private func gradeColor(for level: Int) -> Color {
        switch level {
        case 4: return .green
        case 5: return .blue
        case 8: return .orange
        case 10: return .purple
        case 11: return .red
        default: return .accentColor
        }
    }

    // MARK: - Error View

    private func errorView(_ error: Error) -> some View {
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
    }

    // MARK: - Lesson List

    private var lessonListView: some View {
        List(lessons) { lesson in
            NavigationLink(value: lesson) {
                lessonRow(lesson)
            }
        }
        .listStyle(.insetGrouped)
    }

    private func lessonRow(_ lesson: StructuredLesson) -> some View {
        VStack(alignment: .leading, spacing: 8) {
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

    private func selectGrade(_ grade: Grade) {
        selectedGrade = grade
        loadLessons()
    }

    private func loadLessons() {
        guard let grade = selectedGrade else { return }
        Task {
            do {
                isLoading = true
                error = nil
                lessons = try await repository.loadLessons(for: grade)
            } catch {
                self.error = error
            }
            isLoading = false
        }
    }
}
