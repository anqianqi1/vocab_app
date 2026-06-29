import SwiftUI
import VocabularyContent

struct LessonDetailView: View {
    let lesson: StructuredLesson
    let isWideLayout: Bool

    var body: some View {
        Group {
            if isWideLayout {
                HStack(spacing: 0) {
                    LearnView(lesson: lesson, isWideLayout: true)
                        .frame(maxWidth: .infinity)

                    Divider()

                    ExerciseView(lesson: lesson, isWideLayout: true)
                        .frame(maxWidth: .infinity)
                }
            } else {
                TabView {
                    LearnView(lesson: lesson, isWideLayout: false)
                        .tabItem {
                            Label("Learn", systemImage: "book.fill")
                        }

                    ExerciseView(lesson: lesson, isWideLayout: false)
                        .tabItem {
                            Label("Practice", systemImage: "pencil.and.list.clipboard")
                        }
                }
            }
        }
        .navigationTitle(lesson.title)
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
    }
}
