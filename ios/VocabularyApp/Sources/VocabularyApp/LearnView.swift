import SwiftUI
import VocabularyContent
import VocabularyFeatures

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
        .background(Color(.systemGroupedBackground))
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
        VStack(spacing: 8) {
            if !viewModel.lesson.roots.isEmpty {
                HStack(spacing: 12) {
                    ForEach(viewModel.lesson.roots, id: \.root) { root in
                        rootBadge(root)
                    }
                }
                .padding(.top, isWideLayout ? 4 : 8)
            }
        }
    }

    private func rootBadge(_ root: LessonRoot) -> some View {
        VStack(spacing: 2) {
            Text(root.root)
                .font(isWideLayout ? .title2.bold() : .title3.bold())
                .foregroundStyle(.white)
            Text(root.meaning)
                .font(.caption2)
                .foregroundStyle(.white.opacity(0.8))
                .lineLimit(1)
        }
        .padding(.horizontal, isWideLayout ? 20 : 16)
        .padding(.vertical, isWideLayout ? 12 : 10)
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(LinearGradient(
                    colors: [.purple, .indigo],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                ))
        )
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
                .font(.subheadline.weight(.medium))
                .padding(.horizontal, 14)
                .padding(.vertical, 8)
                .background(
                    RoundedRectangle(cornerRadius: 20)
                        .fill(isSelected ? Color.accentColor : Color(.systemGray6))
                )
                .foregroundStyle(isSelected ? .white : .primary)
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
        VStack {
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
        VStack(spacing: isWideLayout ? 28 : 20) {
            // Word
            Text(word.word)
                .font(.system(size: isWideLayout ? 48 : 36, weight: .bold, design: .rounded))
                .foregroundStyle(.primary)

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
                .font(.subheadline.weight(.medium))
                .foregroundStyle(.secondary)
                .padding(.horizontal, 12)
                .padding(.vertical, 4)
                .background(
                    RoundedRectangle(cornerRadius: 8)
                        .fill(Color(.systemGray5))
                )

            if viewModel.showDefinition {
                Divider()
                    .padding(.horizontal, 20)

                // Definition
                Text(word.definition)
                    .font(isWideLayout ? .title2 : .title3)
                    .multilineTextAlignment(.center)
                    .foregroundStyle(.primary)
                    .padding(.horizontal)

                // Example
                if !word.example.isEmpty {
                    Text(word.example)
                        .font(isWideLayout ? .body : .callout)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                        .italic()
                }
            } else {
                Text("Tap to reveal")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .padding(.top, 8)
            }
        }
        .padding(isWideLayout ? 48 : 32)
        .frame(maxWidth: isWideLayout ? 600 : .infinity)
        .background(
            RoundedRectangle(cornerRadius: 24)
                .fill(Color(.systemBackground))
                .shadow(color: .black.opacity(0.08), radius: 12, y: 4)
        )
        .onTapGesture {
            withAnimation(.easeInOut(duration: 0.3)) {
                viewModel.toggleDefinition()
            }
        }
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
            .buttonStyle(.bordered)
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
            .buttonStyle(.borderedProminent)
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