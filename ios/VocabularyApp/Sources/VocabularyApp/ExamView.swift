import SwiftUI
import AVFoundation
import VocabularyContent
import VocabularyData
import VocabularyFeatures

private let examSpeech = AVSpeechSynthesizer()

struct ExamView: View {
    let grade: Grade
    @Bindable var store: ProfileStore
    let wordRepository: WordRepository

    @State private var vm: ExamViewModel?
    @State private var loading = true
    @State private var recorded = false
    @State private var typed = ""

    var body: some View {
        Group {
            if loading {
                ProgressView("Building your exam…")
            } else if let vm, !vm.isFinished {
                quiz(vm)
            } else if let vm {
                results(vm)
            } else {
                ContentUnavailableView("Not enough words", systemImage: "questionmark", description: Text("Try another grade."))
            }
        }
        .navigationTitle("Weekly Exam")
        .task { await load() }
    }

    private func load() async {
        let words = (try? await wordRepository.loadWords(for: grade)) ?? []
        let questions = QuizBuilder.makeExam(from: words, count: 10)
        vm = questions.isEmpty ? nil : ExamViewModel(questions: questions)
        loading = false
    }

    private func quiz(_ vm: ExamViewModel) -> some View {
        VStack(spacing: 20) {
            ProgressView(value: vm.progress).tint(KidTheme.green)
            if let q = vm.current {
                if q.kind == .pictureToWord, let name = q.imageName,
                   let url = Bundle.module.url(forResource: (name as NSString).deletingPathExtension, withExtension: "png") {
                    AsyncImage(url: url) { $0.resizable().scaledToFit() } placeholder: { Color.clear }
                        .frame(height: 200).clipShape(RoundedRectangle(cornerRadius: 20))
                    Text("What word is this?").font(.title3.bold())
                } else {
                    HStack(spacing: 8) {
                        Text(q.prompt).font(.system(.title2, design: .rounded).bold()).multilineTextAlignment(.center).padding()
                        Button { speakMasked(q.prompt) } label: { Image(systemName: "speaker.wave.2.fill").foregroundStyle(KidTheme.blue) }
                    }
                }
                if q.kind == .typeTheWord {
                    TextField("Type the word", text: $typed)
                        .textFieldStyle(.roundedBorder).font(.title3).autocorrectionDisabled()
                    Button("Check") { vm.choose(typed.trimmingCharacters(in: .whitespaces)) }
                        .buttonStyle(BigButtonStyle(color: KidTheme.blue)).disabled(vm.hasAnswered)
                    if vm.hasAnswered {
                        Text(vm.isCorrect(typed) ? "✅ Correct!" : "Answer: \(q.answer)").font(.headline)
                    }
                } else {
                    ForEach(q.options, id: \.self) { opt in
                        Button { vm.choose(opt) } label: { Text(opt).frame(maxWidth: .infinity) }
                            .buttonStyle(BigButtonStyle(color: optionColor(vm, opt)))
                            .disabled(vm.hasAnswered)
                    }
                }
                if vm.hasAnswered {
                    Button("Next") { vm.advance(); typed = "" }.buttonStyle(BigButtonStyle(color: KidTheme.purple))
                }
            }
            Spacer()
        }.padding()
    }

    private func optionColor(_ vm: ExamViewModel, _ opt: String) -> Color {
        guard vm.hasAnswered else { return KidTheme.blue }
        if vm.isCorrect(opt) { return KidTheme.green }
        if vm.selected == opt { return KidTheme.pink }
        return .gray
    }

    private func speakMasked(_ text: String) {
        let spoken = text.replacingOccurrences(of: "_____", with: "blank")
        if examSpeech.isSpeaking { examSpeech.stopSpeaking(at: .immediate) }
        let u = AVSpeechUtterance(string: spoken); u.rate = 0.4; u.voice = AVSpeechSynthesisVoice(language: "en-US")
        examSpeech.speak(u)
    }

    private func results(_ vm: ExamViewModel) -> some View {
        VStack(spacing: 18) {
            Text(vm.result.passed ? "🎉" : "💪").font(.system(size: 90))
            Text(vm.result.passed ? "Great job!" : "Keep practicing!").font(.system(.largeTitle, design: .rounded).bold())
            Text("\(vm.result.correct)/\(vm.result.total) correct").font(.title2)
            Text("+\(vm.result.xpEarned) XP").font(.title.bold()).foregroundStyle(KidTheme.green)
        }
        .onAppear { if !recorded { store.recordExam(vm.result); recorded = true } }
    }
}
