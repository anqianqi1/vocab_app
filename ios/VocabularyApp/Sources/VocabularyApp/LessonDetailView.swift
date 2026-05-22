import SwiftUI
import VocabularyContent

struct LessonDetailView: View {
    let lesson: StructuredLesson

    var body: some View {
        TabView {
            LearnView(lesson: lesson)
                .tabItem {
                    Label("Learn", systemImage: "book.fill")
                }

            ExerciseView(lesson: lesson)
                .tabItem {
                    Label("Practice", systemImage: "pencil.and.list.clipboard")
                }
        }
        .navigationTitle(lesson.title)
        #if os(iOS)
        .navigationBarTitleDisplayMode(.large)
        #endif
    }
}