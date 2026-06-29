import SwiftUI
import VocabularyContent
import VocabularyData

/// Grade-scoped lesson list that lives inside Home's navigation stack (no nested
/// stack, no second grade picker). Tapping a lesson pushes its detail.
struct LessonsView: View {
    let grade: Grade
    let repository: StructuredLessonRepository
    let wordRepository: WordRepository

    @State private var lessons: [StructuredLesson] = []
    @State private var isLoading = true

    var body: some View {
        Group {
            if isLoading {
                ProgressView("Loading lessons…")
            } else if lessons.isEmpty {
                ContentUnavailableView("No lessons", systemImage: "book", description: Text("Try another grade."))
            } else {
                ScrollView {
                    VStack(spacing: 14) {
                        ForEach(Array(lessons.enumerated()), id: \.element.id) { idx, lesson in
                            NavigationLink {
                                LessonDetailView(lesson: lesson, isWideLayout: false)
                            } label: {
                                HStack(spacing: 14) {
                                    Text("\(lesson.lessonNumber)")
                                        .font(.system(.title, design: .rounded).bold())
                                        .foregroundStyle(.white)
                                        .frame(width: 56, height: 56)
                                        .background(KidTheme.gradeColor((idx % 6) + 1), in: Circle())
                                    VStack(alignment: .leading, spacing: 4) {
                                        Text(lesson.title).font(.system(.headline, design: .rounded).bold())
                                            .foregroundStyle(.primary).lineLimit(2)
                                        Text("⭐ \(lesson.totalWordCount) words").font(.subheadline).foregroundStyle(.secondary)
                                    }
                                    Spacer()
                                    Image(systemName: "chevron.right").foregroundStyle(.secondary)
                                }
                                .padding(16)
                                .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 22))
                            }
                            .buttonStyle(.plain)
                        }
                    }
                    .padding()
                }
            }
        }
        .navigationTitle("Grade \(grade.level)")
        .task { await load() }
    }

    private func load() async {
        let loaded = (try? await repository.loadLessons(for: grade)) ?? []
        let words = (try? await wordRepository.loadWords(for: grade)) ?? []
        lessons = merge(words, into: loaded)
        isLoading = false
    }

    private func merge(_ words: [WordEntry], into lessons: [StructuredLesson]) -> [StructuredLesson] {
        guard !words.isEmpty else { return lessons }
        let byLesson = Dictionary(grouping: words, by: \.lessonNumber)
        return lessons.map { lesson in
            guard let lw = byLesson[lesson.lessonNumber], !lw.isEmpty else { return lesson }
            return StructuredLesson(
                lessonNumber: lesson.lessonNumber, title: lesson.title, roots: lesson.roots,
                keyWords: lw.filter { $0.group == .key }.map(\.word),
                familiarWords: lw.filter { $0.group == .familiar }.map(\.word),
                challengeWords: lw.filter { $0.group == .challenge }.map(\.word),
                wordDetails: lw.map { WordDetail(word: $0.word, group: $0.group, partOfSpeech: $0.partOfSpeech, definition: $0.definition, example: $0.example, imageName: $0.imageName, root: $0.root, rootMeaning: $0.rootMeaning) },
                exercises: lesson.exercises
            )
        }
    }
}
