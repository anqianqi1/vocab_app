import SwiftUI
import VocabularyFeatures

struct CompletionSummaryView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var showCelebrate = false

    let viewModel: CompletionSummaryViewModel
    let onRetake: () -> Void

    var body: some View {
        VStack(spacing: 24) {
            ZStack {
                if showCelebrate {
                    ConfettiView()
                        .transition(.opacity)
                }
                VStack(spacing: 12) {
                    Image(systemName: "star.circle.fill")
                        .font(.system(size: 72))
                        .foregroundStyle(.yellow)
                        .shadow(radius: 8)
                    Text("Great job!")
                        .font(.largeTitle).bold()
                    Text("You reviewed \(viewModel.lesson.title)")
                        .font(.headline)
                        .foregroundStyle(.secondary)
                }
            }
            .frame(maxWidth: .infinity)

            VStack(spacing: 16) {
                ProgressView(value: viewModel.accuracy)
                    .progressViewStyle(.linear)
                HStack {
                    VStack(alignment: .leading) {
                        Text("Mastered")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                        Text("\(viewModel.masteredCount)")
                            .font(.title3)
                    }
                    Spacer()
                    VStack(alignment: .trailing) {
                        Text("Practice again")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                        Text("\(viewModel.needsPracticeCount)")
                            .font(.title3)
                    }
                }
            }
            .padding()
            .background(
                RoundedRectangle(cornerRadius: 20)
                    .fill(summaryBackground)
            )

            Spacer()

            VStack(spacing: 12) {
                Button {
                    onRetake()
                } label: {
                    Text("Retake lesson")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)

                Button("Back to lessons") { dismiss() }
                    .buttonStyle(.bordered)
            }
        }
        .padding()
        .task {
            withAnimation(.easeInOut(duration: 0.6)) {
                showCelebrate = true
            }
        }
    }
}

private struct ConfettiView: View {
    @State private var spins = false

    var body: some View {
        HStack(spacing: 24) {
            ForEach(0..<6) { index in
                Image(systemName: "seal.fill")
                    .foregroundStyle(.pink.opacity(0.8))
                    .rotationEffect(.degrees(spins ? 360 : 0))
                    .animation(.easeInOut(duration: 2).repeatForever().delay(Double(index) * 0.1), value: spins)
            }
        }
        .onAppear { spins = true }
    }
}

private let summaryBackground = Color(.sRGB, white: 0.95, opacity: 1)
