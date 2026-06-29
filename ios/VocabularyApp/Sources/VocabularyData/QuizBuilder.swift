import Foundation
import VocabularyContent

/// Builds a kid-friendly weekly exam from a grade's words.
/// Mixes picture, definition→word, and word→definition questions, with
/// distractors drawn from other real words in the same grade.
public enum QuizBuilder {
    public static func makeExam(from words: [WordEntry], count: Int = 10) -> [ExamQuestion] {
        let usable = words.filter { !$0.word.isEmpty && !$0.definition.isEmpty }
        guard usable.count >= 4 else { return [] }

        var questions: [ExamQuestion] = []
        for word in usable.shuffled() {
            guard questions.count < count else { break }
            let distractors = usable.filter { $0.word != word.word }.shuffled().prefix(3).map(\.word)
            guard distractors.count == 3 else { continue }
            let options = (distractors + [word.word]).shuffled()

            if let image = word.imageName, !image.isEmpty {
                questions.append(ExamQuestion(kind: .pictureToWord, prompt: word.word, imageName: image, answer: word.word, options: options))
            } else {
                let defDistractors = usable.filter { $0.word != word.word && !$0.definition.isEmpty }
                    .shuffled().prefix(3).map(\.definition)
                let masked = mask(word.definition, answer: word.word)
                switch Int.random(in: 0...2) {
                case 0:
                    questions.append(ExamQuestion(kind: .typeTheWord, prompt: masked, imageName: nil, answer: word.word, options: []))
                case 1 where defDistractors.count == 3:
                    questions.append(ExamQuestion(kind: .wordToDefinition, prompt: word.word, imageName: nil, answer: word.definition, options: (defDistractors + [word.definition]).shuffled()))
                default:
                    questions.append(ExamQuestion(kind: .definitionToWord, prompt: masked, imageName: nil, answer: word.word, options: options))
                }
            }
        }
        return questions
    }

    /// Hide the answer word (and simple variants) inside a definition so the
    /// question never gives itself away.
    private static func mask(_ text: String, answer: String) -> String {
        guard answer.count > 2 else { return text }
        var result = text
        let stem = String(answer.dropLast(min(3, answer.count - 3)))
        for token in [answer, stem].filter({ $0.count > 2 }) {
            if let range = result.range(of: token, options: .caseInsensitive) {
                result.replaceSubrange(range, with: "_____")
            }
        }
        return result
    }
}
