import SwiftUI
import VocabularyContent

struct LessonDetailView: View {
    let lesson: StructuredLesson

    @Environment(\.horizontalSizeClass) private var horizontalSizeClass

    private var isIPad: Bool { horizontalSizeClass == .regular }

    var body: some View {
        Group {
            if isIPad {
                HStack(spacing: 0) {
                    LearnView(lesson: lesson)
                        .frame(maxWidth: .infinity)

                    Divider()

                    ExerciseView(lesson: lesson)
                        .frame(maxWidth: .infinity)
                }
            } else {
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
            }
        }
        .navigationTitle(lesson.title)
        #if os(iOS)
        .navigationBarTitleDisplayMode(.large)
        #endif
    }
}
