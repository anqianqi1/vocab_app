import Foundation
import Observation
import VocabularyContent

@MainActor
@Observable
public final class ExerciseViewModel {
    public let lesson: StructuredLesson
    public private(set) var questions: [QuizQuestion] = []
    public private(set) var currentIndex: Int = 0
    public private(set) var score: Int = 0
    public private(set) var selectedAnswer: String?
    public private(set) var isAnswerRevealed: Bool = false
    public private(set) var isComplete: Bool = false

    public var currentQuestion: QuizQuestion? {
        guard currentIndex < questions.count else { return nil }
        return questions[currentIndex]
    }

    public var progress: String {
        guard !questions.isEmpty else { return "0 of 0" }
        return "\(currentIndex + 1) of \(questions.count)"
    }

    public var progressFraction: Double {
        guard !questions.isEmpty else { return 0 }
        return Double(currentIndex + 1) / Double(questions.count)
    }

    public var totalQuestions: Int {
        questions.count
    }

    public init(lesson: StructuredLesson) {
        self.lesson = lesson
        generateQuestions()
    }

    /// Generate multiple-choice questions from the lesson's word details.
    /// Each question shows a word and asks the user to pick the correct definition.
    private func generateQuestions() {
        let words = lesson.wordDetails.shuffled()
        let allDefinitions = lesson.wordDetails.map { $0.definition }

        questions = words.map { word in
            // Pick 3 distractors (definitions from other words)
            var distractors = allDefinitions.filter { $0 != word.definition }.shuffled()
            if distractors.count > 3 {
                distractors = Array(distractors.prefix(3))
            }
            // If we don't have enough distractors, pad with empty strings
            while distractors.count < 3 {
                distractors.append("—")
            }

            var options = distractors + [word.definition]
            options.shuffle()

            return QuizQuestion(
                id: word.id,
                word: word.word,
                correctDefinition: word.definition,
                options: options
            )
        }
    }

    /// Submit an answer for the current question.
    public func submitAnswer(_ answer: String) {
        guard !isAnswerRevealed, let question = currentQuestion else { return }
        selectedAnswer = answer
        isAnswerRevealed = true

        if answer == question.correctDefinition {
            score += 1
        }
    }

    /// Move to the next question or mark as complete.
    public func nextQuestion() {
        selectedAnswer = nil
        isAnswerRevealed = false

        if currentIndex + 1 < questions.count {
            currentIndex += 1
        } else {
            isComplete = true
        }
    }

    /// Reset the entire exercise.
    public func reset() {
        currentIndex = 0
        score = 0
        selectedAnswer = nil
        isAnswerRevealed = false
        isComplete = false
        generateQuestions()
    }
}

/// A single multiple-choice quiz question.
public struct QuizQuestion: Identifiable, Hashable {
    public let id: String
    public let word: String
    public let correctDefinition: String
    public let options: [String]

    public init(id: String, word: String, correctDefinition: String, options: [String]) {
        self.id = id
        self.word = word
        self.correctDefinition = correctDefinition
        self.options = options
    }
}