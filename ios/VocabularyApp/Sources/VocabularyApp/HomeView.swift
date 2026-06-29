import SwiftUI
import VocabularyContent
import VocabularyData

struct HomeView: View {
    @Bindable var store: ProfileStore
    let lessonRepository: StructuredLessonRepository
    let wordRepository: WordRepository

    @State private var grade = Grade(level: 4)
    private let available: Set<Int> = [4, 5]

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 22) {
                    if let kid = store.current { heroCard(kid) }
                    gradePicker
                    actions
                }
                .padding()
            }
            .navigationTitle("Word Heroes")
            .background(Color(.systemGroupedBackground))
        }
    }

    private func heroCard(_ kid: PlayerProfile) -> some View {
        VStack(spacing: 10) {
            HStack(spacing: 14) {
                Text(kid.avatar).font(.system(size: 54))
                VStack(alignment: .leading, spacing: 2) {
                    Text("Hi, \(kid.name)!").font(.system(.title, design: .rounded).bold())
                    Text("Level \(kid.level)").font(.headline).foregroundStyle(.secondary)
                }
                Spacer()
                VStack { Text("🔥 \(kid.streakDays)").font(.title3.bold()); Text("streak").font(.caption2) }
            }
            ProgressView(value: Double(kid.xpIntoLevel), total: 100).tint(KidTheme.green)
            Text("\(kid.xpIntoLevel)/100 XP to next level").font(.caption).foregroundStyle(.secondary)
        }
        .padding().background(.thinMaterial, in: RoundedRectangle(cornerRadius: 22))
    }

    private var gradePicker: some View {
        VStack(alignment: .leading) {
            Text("Pick a grade").font(.headline)
            LazyVGrid(columns: Array(repeating: GridItem(), count: 3), spacing: 12) {
                ForEach(1...6, id: \.self) { lvl in
                    Button { if available.contains(lvl) { grade = Grade(level: lvl) } } label: {
                        Text("\(lvl)").font(.system(.title, design: .rounded).bold())
                            .frame(maxWidth: .infinity, minHeight: 60)
                            .background(KidTheme.gradeColor(lvl).opacity(available.contains(lvl) ? 1 : 0.25),
                                        in: RoundedRectangle(cornerRadius: 18))
                            .foregroundStyle(.white)
                            .overlay(grade.level == lvl ? RoundedRectangle(cornerRadius: 18).stroke(.primary, lineWidth: 3) : nil)
                    }.disabled(!available.contains(lvl))
                }
            }
            Text("Grades 4 & 5 ready. More coming soon!").font(.caption).foregroundStyle(.secondary)
        }
    }

    private var actions: some View {
        VStack(spacing: 14) {
            NavigationLink { LessonsView(grade: grade, repository: lessonRepository, wordRepository: wordRepository) } label: { Text("📖 Learn Words") }
                .buttonStyle(BigButtonStyle(color: KidTheme.blue))
            NavigationLink { ExamView(grade: grade, store: store, wordRepository: wordRepository) } label: {
                Text(store.tookExamThisWeek() ? "✅ Weekly Exam Done" : "📝 Weekly Exam")
            }.buttonStyle(BigButtonStyle(color: KidTheme.orange))
            NavigationLink { LeaderboardView(store: store) } label: { Text("🏆 Leaderboard") }
                .buttonStyle(BigButtonStyle(color: KidTheme.purple))
        }
    }
}
