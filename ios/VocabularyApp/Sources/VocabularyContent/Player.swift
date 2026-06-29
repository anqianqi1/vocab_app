import Foundation

/// An on-device kid profile (no login). Stores progress used for XP, streaks,
/// and the local leaderboard.
public struct PlayerProfile: Identifiable, Hashable, Codable {
    public let id: UUID
    public var name: String
    public var avatar: String        // emoji
    public var totalXP: Int
    public var streakDays: Int
    public var lastExamISOWeek: String?   // e.g. "2026-W26" to gate one exam/week
    public var bestWeeklyXP: Int
    public var isSimulated: Bool

    public init(
        id: UUID = UUID(),
        name: String,
        avatar: String,
        totalXP: Int = 0,
        streakDays: Int = 0,
        lastExamISOWeek: String? = nil,
        bestWeeklyXP: Int = 0,
        isSimulated: Bool = false
    ) {
        self.id = id
        self.name = name
        self.avatar = avatar
        self.totalXP = totalXP
        self.streakDays = streakDays
        self.lastExamISOWeek = lastExamISOWeek
        self.bestWeeklyXP = bestWeeklyXP
        self.isSimulated = isSimulated
    }

    /// Fun avatars kids can pick from.
    public static let avatarChoices = ["🦊", "🐼", "🦁", "🐯", "🐨", "🦄", "🐸", "🐵", "🐶", "🐱", "🦉", "🐢"]

    public var level: Int { max(1, totalXP / 100 + 1) }
    public var xpIntoLevel: Int { totalXP % 100 }
}
