import SwiftUI
import VocabularyContent
import VocabularyFeatures

struct ReviewSessionView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var viewModel: ReviewSessionViewModel
    let lesson: Lesson

    init(viewModel: ReviewSessionViewModel, lesson: Lesson) {
        _viewModel = State(initialValue: viewModel)
        self.lesson = lesson
    }

    var body: some View {
        VStack(spacing: 24) {
            if let entry = viewModel.currentEntry {
                VStack(spacing: 16) {
                    Text(entry.term)
                        .font(.largeTitle)
                        .bold()
                    if viewModel.showDefinition {
                        VStack(spacing: 8) {
                            Text(entry.definition)
                                .font(.title3)
                                .multilineTextAlignment(.center)
                            if let example = entry.example, !example.isEmpty {
                                Text(example)
                                    .font(.callout)
                                    .foregroundStyle(.secondary)
                                    .multilineTextAlignment(.center)
                            }
                        }
                        .transition(.opacity)
                    } else {
                        Text("Tap to reveal definition")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                }
                .padding()
                .frame(maxWidth: .infinity)
                .background(
                    RoundedRectangle(cornerRadius: 20)
                        .fill(cardBackground)
                )
                .onTapGesture { viewModel.toggleCard() }
                Spacer()
                HStack(spacing: 20) {
                    Button {
                        viewModel.markNeedsPractice()
                    } label: {
                        Text("Practice again")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.bordered)

                    Button {
                        viewModel.markKnown()
                    } label: {
                        Text("I know this")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                }
            } else {
                Spacer()
                CompletionSummaryView(
                    viewModel: CompletionSummaryViewModel(
                        lesson: lesson,
                        mastered: viewModel.masteredCards.count,
                        needsPractice: viewModel.needsPracticeCards.count
                    ),
                    onRetake: {
                        viewModel.reset()
                    }
                )
            }
        }
        .padding()
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
    }
}

private let cardBackground = Color(.sRGB, white: 0.95, opacity: 1)
