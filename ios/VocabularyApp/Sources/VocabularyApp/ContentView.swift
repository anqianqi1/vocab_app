import SwiftUI
import VocabularyContent
import VocabularyData

struct ContentView: View {
    @State private var selectedGrade: Grade?
    @State private var lessons: [StructuredLesson] = []
    @State private var isLoading = false
    @State private var error: Error?
    @State private var selectedLesson: StructuredLesson?

    private let repository: StructuredLessonRepository

    init(repository: StructuredLessonRepository) {
        self.repository = repository
    }

    var body: some View {
        GeometryReader { geometry in
            if geometry.size.width >= 640 {
                iPadLayout(geometry: geometry)
            } else {
                iPhoneLayout
            }
        }
    }

    // MARK: - iPad Layout

    private func iPadLayout(geometry: GeometryProxy) -> some View {
        HStack(spacing: 0) {
            // Sidebar
            VStack(spacing: 0) {
                // Header
                if selectedGrade == nil {
                    sidebarHeader("Grades")
                } else {
                    sidebarHeader("Grade \(selectedGrade?.level ?? 0)")
                }

                // Content
                if selectedGrade == nil {
                    List(Grade.supportedGrades) { grade in
                        Button {
                            selectGrade(grade)
                        } label: {
                            Label {
                                Text(grade.displayName)
                                    .foregroundStyle(.primary)
                            } icon: {
                                Image(systemName: "\(grade.level).circle.fill")
                                    .foregroundStyle(gradeColor(for: grade.level))
                            }
                        }
                    }
                    .listStyle(.sidebar)
                } else if isLoading && lessons.isEmpty {
                    Spacer()
                    ProgressView("Loading lessons…")
                    Spacer()
                } else if let error {
                    errorView(error)
                } else {
                    List(lessons) { lesson in
                        Button {
                            selectedLesson = lesson
                        } label: {
                            lessonRow(lesson)
                        }
                        .buttonStyle(.plain)
                        .listRowBackground(
                            selectedLesson?.id == lesson.id
                                ? Color.accentColor.opacity(0.1)
                                : Color.clear
                        )
                    }
                    .listStyle(.sidebar)
                }

                // Bottom toolbar
                if selectedGrade != nil {
                    Divider()
                    HStack {
                        Button {
                            selectedGrade = nil
                            lessons = []
                            selectedLesson = nil
                        } label: {
                            Label("All Grades", systemImage: "chevron.left")
                        }
                        Spacer()
                        Button {
                            loadLessons()
                        } label: {
                            Label("Refresh", systemImage: "arrow.clockwise")
                        }
                    }
                    .padding(.horizontal, 16)
                    .padding(.vertical, 10)
                    .background(.bar)
                }
            }
            .frame(width: min(320, geometry.size.width * 0.32))
            .background(Color(.systemGroupedBackground))

            Divider()

            // Detail
            detailView
                .frame(maxWidth: .infinity)
                .background(Color(.systemBackground))
        }
    }

    private func sidebarHeader(_ title: String) -> some View {
        Text(title)
            .font(.title2.weight(.bold))
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .background(.bar)
    }

    // MARK: - Detail

    @ViewBuilder
    private var detailView: some View {
        if selectedGrade == nil {
            welcomeView
        } else if let lesson = selectedLesson {
            LessonDetailView(lesson: lesson)
        } else {
            emptySelectionView
        }
    }

    private var welcomeView: some View {
        VStack(spacing: 24) {
            Spacer()
            Image(systemName: "book.pages.fill")
                .font(.system(size: 80))
                .foregroundStyle(.blue)
            Text("Vocabulary Builder")
                .font(.largeTitle.bold())
            Text("Select a grade from the sidebar\nto start learning")
                .font(.title3)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
            Spacer()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(.systemGroupedBackground))
    }

    private var emptySelectionView: some View {
        VStack(spacing: 16) {
            Image(systemName: "text.book.closed.fill")
                .font(.system(size: 64))
                .foregroundStyle(.secondary.opacity(0.5))
            Text("Select a Lesson")
                .font(.title2)
                .foregroundStyle(.secondary)
            Text("Choose a lesson from the sidebar to start learning and practicing vocabulary.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 40)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(.systemGroupedBackground))
    }

    // MARK: - iPhone Layout

    private var iPhoneLayout: some View {
        NavigationStack {
            Group {
                if selectedGrade == nil {
                    iPhoneGradePicker
                } else if isLoading && lessons.isEmpty {
                    ProgressView("Loading lessons…")
                } else if let error {
                    errorView(error)
                } else {
                    iPhoneLessonList
                }
            }
            .navigationTitle(selectedGrade.map { "Grade \($0.level)" } ?? "Vocabulary")
            .toolbar {
                if selectedGrade != nil {
                    ToolbarItem(placement: .navigationBarLeading) {
                        Button {
                            selectedGrade = nil
                            lessons = []
                            selectedLesson = nil
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

    private var iPhoneGradePicker: some View {
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
                        .frame(maxWidth: 500)
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
        .frame(maxWidth: .infinity)
        .background(Color(.systemGroupedBackground))
    }

    private var iPhoneLessonList: some View {
        List(lessons) { lesson in
            NavigationLink(value: lesson) {
                lessonRow(lesson)
            }
        }
        .listStyle(.insetGrouped)
    }

    // MARK: - Shared Views

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

    private func lessonRow(_ lesson: StructuredLesson) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text("Lesson \(lesson.lessonNumber)")
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.white)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(
                        RoundedRectangle(cornerRadius: 4)
                            .fill(Color.accentColor)
                    )
                Text(lesson.title)
                    .font(.subheadline.weight(.medium))
                    .lineLimit(2)
            }
            if !lesson.roots.isEmpty {
                HStack(spacing: 4) {
                    ForEach(lesson.roots, id: \.root) { root in
                        Text(root.root)
                            .font(.caption2.weight(.medium))
                            .foregroundStyle(.purple)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 1)
                            .background(
                                RoundedRectangle(cornerRadius: 3)
                                    .fill(.purple.opacity(0.1))
                            )
                    }
                }
            }
            HStack(spacing: 8) {
                wordCountBadge(label: "Key", count: lesson.keyWords.count, color: .green)
                wordCountBadge(label: "Familiar", count: lesson.familiarWords.count, color: .blue)
                wordCountBadge(label: "Challenge", count: lesson.challengeWords.count, color: .orange)
            }
        }
        .padding(.vertical, 4)
    }

    private func wordCountBadge(label: String, count: Int, color: Color) -> some View {
        HStack(spacing: 3) {
            Circle()
                .fill(color)
                .frame(width: 6, height: 6)
            Text("\(count) \(label)")
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
    }

    // MARK: - Helpers

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

    private func selectGrade(_ grade: Grade) {
        selectedGrade = grade
        selectedLesson = nil
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
