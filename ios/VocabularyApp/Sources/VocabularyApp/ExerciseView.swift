import SwiftUI
import VocabularyContent
import VocabularyFeatures

struct ExerciseView: View {
    @State private var viewModel: ExerciseViewModel

    init(lesson: StructuredLesson) {
        _viewModel = State(initialValue: ExerciseViewModel(lesson: lesson))
    }

    var body: some View {
        VStack(spacing: 0) {
            if viewModel.isComplete {
                completionView
            } else if let question = viewModel.currentQuestion {
                questionView(question)
            } else {
                ContentUnavailableView(
                    "No Questions",
                    systemImage: "questionmark.circle",
                    description: Text("This lesson has no words to practice.")
                )
            }
        }
        .background(Color(.systemGroupedBackground))
    }

    // MARK: - Question View

    private func questionView(_ question: QuizQuestion) -> some View {
        VStack(spacing: 0) {
            // Progress
            progressSection

            Spacer()

            // Word prompt
            VStack(spacing: 8) {
                Text("What does this word mean?")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)

                Text(question.word)
                    .font(.system(size: 40, weight: .bold, design: .rounded))
                    .foregroundStyle(.primary)
            }
            .padding(.bottom, 32)

            // Answer options
            VStack(spacing: 12) {
                ForEach(question.options, id: \.self) { option in
                    answerButton(option, question: question)
                }
            }
            .padding(.horizontal)

            Spacer()

            // Next button (only after answering)
            if viewModel.isAnswerRevealed {
                Button {
                    withAnimation(.spring(response: 0.4, dampingFraction: 0.8)) {
                        viewModel.nextQuestion()
                    }
                } label: {
                    Label("Next", systemImage: "arrow.right")
                        .font(.headline)
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .padding(.horizontal)
                .padding(.bottom, 16)
                .transition(.move(edge: .bottom).combined(with: .opacity))
            }
        }
        .animation(.spring(response: 0.4, dampingFraction: 0.8), value: viewModel.currentIndex)
    }

    // MARK: - Progress

    private var progressSection: some View {
        VStack(spacing: 6) {
            ProgressView(value: viewModel.progressFraction)
                .tint(.accentColor)
            HStack {
                Text(viewModel.progress)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Spacer()
                Text("Score: \(viewModel.score)")
                    .font(.caption.weight(.medium))
                    .foregroundStyle(.blue)
            }
        }
        .padding()
    }

    // MARK: - Answer Button

    private func answerButton(_ option: String, question: QuizQuestion) -> some View {
        Button {
            withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) {
                viewModel.submitAnswer(option)
            }
        } label: {
            HStack {
                Text(option)
                    .font(.body)
                    .multilineTextAlignment(.leading)
                    .foregroundStyle(buttonTextColor(for: option, question: question))
                Spacer()
                if viewModel.isAnswerRevealed {
                    buttonIcon(for: option, question: question)
                }
            }
            .padding(16)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(
                RoundedRectangle(cornerRadius: 16)
                    .fill(buttonBackgroundColor(for: option, question: question))
            )
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .stroke(buttonBorderColor(for: option, question: question), lineWidth: 2)
            )
        }
        .disabled(viewModel.isAnswerRevealed)
    }

    private func buttonBackgroundColor(for option: String, question: QuizQuestion) -> Color {
        guard viewModel.isAnswerRevealed else {
            return Color(.systemBackground)
        }

        if option == question.correctDefinition {
            return .green.opacity(0.15)
        }
        if option == viewModel.selectedAnswer && option != question.correctDefinition {
            return .red.opacity(0.15)
        }
        return Color(.systemBackground).opacity(0.5)
    }

    private func buttonBorderColor(for option: String, question: QuizQuestion) -> Color {
        guard viewModel.isAnswerRevealed else {
            return Color(.systemGray4)
        }

        if option == question.correctDefinition {
            return .green
        }
        if option == viewModel.selectedAnswer && option != question.correctDefinition {
            return .red
        }
        return Color(.systemGray4)
    }

    private func buttonTextColor(for option: String, question: QuizQuestion) -> Color {
        guard viewModel.isAnswerRevealed else { return .primary }
        if option == question.correctDefinition { return .green }
        if option == viewModel.selectedAnswer && option != question.correctDefinition { return .red }
        return .secondary
    }

    private func buttonIcon(for option: String, question: QuizQuestion) -> some View {
        if option == question.correctDefinition {
            return Image(systemName: "checkmark.circle.fill")
                .foregroundStyle(.green)
        } else if option == viewModel.selectedAnswer && option != question.correctDefinition {
            return Image(systemName: "xmark.circle.fill")
                .foregroundStyle(.red)
        }
        return Image(systemName: "circle")
            .foregroundStyle(.clear)
    }

    // MARK: - Completion View

    private var completionView: some View {
        VStack(spacing: 24) {
            Spacer()

            // Celebration icon
            ZStack {
                Circle()
                    .fill(LinearGradient(
                        colors: [.yellow, .orange],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    ))
                    .frame(width: 100, height: 100)

                Image(systemName: viewModel.score == viewModel.totalQuestions ? "trophy.fill" : "star.fill")
                    .font(.system(size: 48))
                    .foregroundStyle(.white)
            }
            .shadow(color: .orange.opacity(0.3), radius: 16, y: 8)

            Text(viewModel.score == viewModel.totalQuestions ? "Perfect!" : "Great job!")
                .font(.largeTitle.bold())

            Text("You got \(viewModel.score) out of \(viewModel.totalQuestions) correct")
                .font(.title3)
                .foregroundStyle(.secondary)

            // Score ring
            ZStack {
                Circle()
                    .stroke(Color(.systemGray5), lineWidth: 12)
                    .frame(width: 120, height: 120)

                Circle()
                    .trim(from: 0, to: CGFloat(viewModel.score) / CGFloat(max(viewModel.totalQuestions, 1)))
                    .stroke(
                        LinearGradient(colors: [.green, .mint], startPoint: .top, endPoint: .bottom),
                        style: StrokeStyle(lineWidth: 12, lineCap: .round)
                    )
                    .frame(width: 120, height: 120)
                    .rotationEffect(.degrees(-90))
                    .animation(.easeInOut(duration: 1.0), value: viewModel.isComplete)

                Text("\(Int(Double(viewModel.score) / Double(max(viewModel.totalQuestions, 1)) * 100))%")
                    .font(.title2.bold())
            }

            Spacer()

            VStack(spacing: 12) {
                Button {
                    withAnimation(.spring(response: 0.4, dampingFraction: 0.8)) {
                        viewModel.reset()
                    }
                } label: {
                    Label("Try Again", systemImage: "arrow.counterclockwise")
                        .font(.headline)
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
            }
            .padding(.horizontal)
            .padding(.bottom, 32)
        }
        .padding()
    }
}