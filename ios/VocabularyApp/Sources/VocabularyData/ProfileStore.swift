import Foundation
import Observation
import VocabularyContent

/// On-device profile + score storage (no login). Persists to UserDefaults as JSON.
/// Also seeds a few friendly "classmate" profiles so the leaderboard isn't empty.
@MainActor
@Observable
public final class ProfileStore {
    public private(set) var profiles: [PlayerProfile] = []
    public private(set) var currentID: UUID?

    private let defaults: UserDefaults
    private let profilesKey = "vocab.profiles.v1"
    private let currentKey = "vocab.currentProfile.v1"

    public init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        load()
        if profiles.filter({ !$0.isSimulated }).isEmpty {
            seedClassmates()
        }
    }

    public var current: PlayerProfile? {
        profiles.first { $0.id == currentID }
    }

    public func select(_ profile: PlayerProfile) {
        currentID = profile.id
        persist()
    }

    @discardableResult
    public func addProfile(name: String, avatar: String) -> PlayerProfile {
        let profile = PlayerProfile(name: name, avatar: avatar)
        profiles.append(profile)
        currentID = profile.id
        persist()
        return profile
    }

    /// Apply an exam result to the current player: add XP, update streak, gate by week.
    public func recordExam(_ result: ExamResult) {
        guard let index = profiles.firstIndex(where: { $0.id == currentID }) else { return }
        var profile = profiles[index]
        let week = Self.currentISOWeek()
        profile.totalXP += result.xpEarned
        profile.bestWeeklyXP = max(profile.bestWeeklyXP, result.xpEarned)
        profile.streakDays = (profile.lastExamISOWeek == nil) ? 1 : profile.streakDays + 1
        profile.lastExamISOWeek = week
        profiles[index] = profile
        persist()
    }

    public func tookExamThisWeek() -> Bool {
        current?.lastExamISOWeek == Self.currentISOWeek()
    }

    /// Profiles sorted by XP for the leaderboard.
    public func leaderboard() -> [PlayerProfile] {
        profiles.sorted { $0.totalXP > $1.totalXP }
    }

    public func rank(of profile: PlayerProfile) -> Int {
        (leaderboard().firstIndex(of: profile) ?? 0) + 1
    }

    public static func currentISOWeek(date: Date = Date()) -> String {
        var cal = Calendar(identifier: .iso8601)
        cal.timeZone = .current
        let week = cal.component(.weekOfYear, from: date)
        let year = cal.component(.yearForWeekOfYear, from: date)
        return String(format: "%04d-W%02d", year, week)
    }

    private func seedClassmates() {
        profiles += [
            PlayerProfile(name: "Mia", avatar: "🦄", totalXP: 240, streakDays: 3, bestWeeklyXP: 90, isSimulated: true),
            PlayerProfile(name: "Leo", avatar: "🦁", totalXP: 180, streakDays: 2, bestWeeklyXP: 70, isSimulated: true),
            PlayerProfile(name: "Ava", avatar: "🐼", totalXP: 120, streakDays: 1, bestWeeklyXP: 60, isSimulated: true),
        ]
        persist()
    }

    private func load() {
        if let data = defaults.data(forKey: profilesKey),
           let saved = try? JSONDecoder().decode([PlayerProfile].self, from: data) {
            profiles = saved
        }
        if let raw = defaults.string(forKey: currentKey) {
            currentID = UUID(uuidString: raw)
        }
    }

    private func persist() {
        if let data = try? JSONEncoder().encode(profiles) {
            defaults.set(data, forKey: profilesKey)
        }
        defaults.set(currentID?.uuidString, forKey: currentKey)
    }
}
