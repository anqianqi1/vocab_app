import SwiftUI
import AVFoundation
import VocabularyContent
import VocabularyFeatures

private let speechSynth = AVSpeechSynthesizer()

struct LearnView: View {
    @State private var viewModel: LearnViewModel
    let isWideLayout: Bool

    init(lesson: StructuredLesson, isWideLayout: Bool = false) {
        _viewModel = State(initialValue: LearnViewModel(lesson: lesson))
        self.isWideLayout = isWideLayout
    }

    var body: some View {
        VStack(spacing: 0) {
            // Title header (shown on iPad since there's no tab label)
            if isWideLayout {
                headerView
            }

            // Root info header
            rootInfoHeader

            // Group selector
            groupSelector

            // Progress bar
            progressSection

            // Flashcard
            Spacer(minLength: 16)
            flashcardSection
            Spacer(minLength: 16)

            // Navigation buttons
            navigationButtons
        }
        .padding(.horizontal, isWideLayout ? 32 : 16)
        .padding(.bottom, 16)
        .background(LinearGradient(colors: [KidTheme.blue.opacity(0.18), KidTheme.purple.opacity(0.12)], startPoint: .top, endPoint: .bottom).ignoresSafeArea())
    }

    // MARK: - Header (iPad)

    private var headerView: some View {
        HStack {
            Label("Learn", systemImage: "book.fill")
                .font(.title3.weight(.semibold))
                .foregroundStyle(.primary)
            Spacer()
        }
        .padding(.top, 12)
        .padding(.bottom, 4)
    }

    // MARK: - Root Info

    private var rootInfoHeader: some View {
        EmptyView()
    }

    // MARK: - Group Selector

    private var groupSelector: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                groupChip("All Words", icon: "text.book.closed.fill", isSelected: viewModel.selectedGroup == nil) {
                    viewModel.selectGroup(nil)
                }

                ForEach(WordGroup.allCases, id: \.self) { group in
                    groupChip(group.displayName, icon: group.icon, isSelected: viewModel.selectedGroup == group) {
                        viewModel.selectGroup(group)
                    }
                }
            }
            .padding(.vertical, 12)
        }
    }

    private func groupChip(_ title: String, icon: String, isSelected: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Label(title, systemImage: icon)
                .font(.system(.subheadline, design: .rounded).weight(.bold))
                .padding(.horizontal, 16)
                .padding(.vertical, 10)
                .background(
                    Capsule().fill(isSelected ? KidTheme.purple : Color.white.opacity(0.7))
                )
                .foregroundStyle(isSelected ? .white : KidTheme.purple)
        }
    }

    // MARK: - Progress

    private var progressSection: some View {
        VStack(spacing: 6) {
            ProgressView(value: viewModel.progressFraction)
                .tint(.accentColor)
            Text(viewModel.progress)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }

    // MARK: - Flashcard

    private var flashcardSection: some View {
        ScrollView {
            if let word = viewModel.currentWord {
                flashcard(for: word)
                    .transition(.asymmetric(
                        insertion: .move(edge: .trailing).combined(with: .opacity),
                        removal: .move(edge: .leading).combined(with: .opacity)
                    ))
                    .id(word.id)
            } else {
                ContentUnavailableView(
                    "No Words",
                    systemImage: "text.word.spacing",
                    description: Text("Select a different word group to see words.")
                )
            }
        }
        .animation(.spring(response: 0.4, dampingFraction: 0.8), value: viewModel.currentWord?.id)
    }

    private func flashcard(for word: WordDetail) -> some View {
        VStack(spacing: isWideLayout ? 24 : 18) {
            // Root pill matching this word
            if !word.root.isEmpty {
                Text(word.rootMeaning.isEmpty ? word.root : "\(word.root) · \(word.rootMeaning)")
                    .font(.system(.caption, design: .rounded).bold())
                    .foregroundStyle(.white)
                    .lineLimit(1).minimumScaleFactor(0.7)
                    .padding(.horizontal, 14).padding(.vertical, 6)
                    .background(Capsule().fill(KidTheme.purple))
            }
            // Word + tap-to-hear
            HStack(spacing: 10) {
                Text(word.word)
                    .font(.system(size: isWideLayout ? 48 : 36, weight: .bold, design: .rounded))
                    .foregroundStyle(.primary)
                Button { speak(word.word) } label: {
                    Image(systemName: "speaker.wave.2.fill").font(.title2).foregroundStyle(KidTheme.blue)
                }
            }

            // Memory-aid image (shown when available)
            if let imageURL = bundledImageURL(for: word) {
                AsyncImage(url: imageURL) { phase in
                    switch phase {
                    case .success(let image):
                        image
                            .resizable()
                            .scaledToFit()
                            .frame(maxHeight: isWideLayout ? 220 : 160)
                            .clipShape(RoundedRectangle(cornerRadius: 16))
                    default:
                        EmptyView()
                    }
                }
            }

            // Part of speech badge
            Text(word.partOfSpeech)
                .font(.system(.subheadline, design: .rounded).weight(.bold))
                .foregroundStyle(.white)
                .padding(.horizontal, 14)
                .padding(.vertical, 5)
                .background(Capsule().fill(groupColor(word.group)))

            if viewModel.showDefinition {
                // Definition bubble
                Text(word.definition)
                    .font(.system(isWideLayout ? .title2 : .title3, design: .rounded))
                    .multilineTextAlignment(.center)
                    .foregroundStyle(.primary)
                    .fixedSize(horizontal: false, vertical: true)
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(groupColor(word.group).opacity(0.12), in: RoundedRectangle(cornerRadius: 16))

                // Example
                if !word.example.isEmpty {
                    Text("“\(word.example)”")
                        .font(isWideLayout ? .body : .callout)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                        .italic()
                }
            } else {
                Text("👆 Tap to reveal")
                    .font(.system(.headline, design: .rounded).bold())
                    .foregroundStyle(KidTheme.purple)
                    .padding(.top, 8)
            }
        }
        .padding(isWideLayout ? 48 : 32)
        .frame(maxWidth: isWideLayout ? 600 : .infinity)
        .background(
            RoundedRectangle(cornerRadius: 28)
                .fill(Color(.systemBackground))
                .shadow(color: groupColor(word.group).opacity(0.35), radius: 14, y: 6)
        )
        .overlay(RoundedRectangle(cornerRadius: 28).stroke(groupColor(word.group), lineWidth: 4))
        .onTapGesture {
            withAnimation(.easeInOut(duration: 0.3)) {
                viewModel.toggleDefinition()
            }
        }
    }

    private func groupColor(_ group: WordGroup) -> Color {
        switch group {
        case .key: return KidTheme.green
        case .familiar: return KidTheme.blue
        case .challenge: return KidTheme.orange
        }
    }

    private func speak(_ text: String) {
        let utterance = AVSpeechUtterance(string: text)
        utterance.rate = 0.4
        utterance.voice = AVSpeechSynthesisVoice(language: "en-US")
        if speechSynth.isSpeaking { speechSynth.stopSpeaking(at: .immediate) }
        speechSynth.speak(utterance)
    }

    // MARK: - Navigation

    private var navigationButtons: some View {
        HStack(spacing: 20) {
            Button {
                withAnimation(.spring(response: 0.4, dampingFraction: 0.8)) {
                    viewModel.previousWord()
                }
            } label: {
                Label("Previous", systemImage: "chevron.left")
                    .font(.headline)
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(BigButtonStyle(color: .gray.opacity(0.7)))
            .disabled(!viewModel.hasPrevious)

            Button {
                withAnimation(.spring(response: 0.4, dampingFraction: 0.8)) {
                    viewModel.nextWord()
                }
            } label: {
                Label("Next", systemImage: "chevron.right")
                    .font(.headline)
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(BigButtonStyle(color: KidTheme.green))
            .disabled(!viewModel.hasNext)
        }
        .frame(maxWidth: isWideLayout ? 600 : .infinity)
        .padding(.top, 8)
    }

    // MARK: - Image lookup

    private func bundledImageURL(for word: WordDetail) -> URL? {
        guard let imageName = word.imageName, !imageName.isEmpty else { return nil }
        let resource = (imageName as NSString).deletingPathExtension
        let ext = (imageName as NSString).pathExtension
        return Bundle.module.url(
            forResource: resource,
            withExtension: ext.isEmpty ? "png" : ext
        )
    }
}