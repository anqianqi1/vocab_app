import SwiftUI
import VocabularyContent
import VocabularyFeatures

struct LearnView: View {
    @State private var viewModel: LearnViewModel

    @Environment(\.horizontalSizeClass) private var horizontalSizeClass

    private var isIPad: Bool { horizontalSizeClass == .regular }

    init(lesson: StructuredLesson) {
        _viewModel = State(initialValue: LearnViewModel(lesson: lesson))
    }

    var body: some View {
        VStack(spacing: 0) {
            // Title header (shown on iPad since there's no tab label)
            if isIPad {
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
        .padding(.horizontal, isIPad ? 32 : 16)
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
                .padding(.top, isIPad ? 4 : 8)
            }
        }
    }

    private func rootBadge(_ root: LessonRoot) -> some View {
        VStack(spacing: 2) {
            Text(root.root)
                .font(isIPad ? .title2.bold() : .title3.bold())
                .foregroundStyle(.white)
            Text(root.meaning)
                .font(.caption2)
                .foregroundStyle(.white.opacity(0.8))
                .lineLimit(1)
        }
        .padding(.horizontal, isIPad ? 20 : 16)
        .padding(.vertical, isIPad ? 12 : 10)
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
        VStack(spacing: isIPad ? 28 : 20) {
            // Word
            Text(word.word)
                .font(.system(size: isIPad ? 48 : 36, weight: .bold, design: .rounded))
                .foregroundStyle(.primary)

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
                    .font(isIPad ? .title2 : .title3)
                    .multilineTextAlignment(.center)
                    .foregroundStyle(.primary)
                    .padding(.horizontal)

                // Example
                if !word.example.isEmpty {
                    Text(word.example)
                        .font(isIPad ? .body : .callout)
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
        .padding(isIPad ? 48 : 32)
        .frame(maxWidth: isIPad ? 600 : .infinity)
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
        .frame(maxWidth: isIPad ? 600 : .infinity)
        .padding(.top, 8)
    }
}