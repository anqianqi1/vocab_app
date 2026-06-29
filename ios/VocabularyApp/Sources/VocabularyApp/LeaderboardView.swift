import SwiftUI
import VocabularyContent
import VocabularyData

struct LeaderboardView: View {
    @Bindable var store: ProfileStore

    var body: some View {
        List {
            ForEach(Array(store.leaderboard().enumerated()), id: \.element.id) { idx, kid in
                HStack(spacing: 14) {
                    Text(medal(idx)).font(.title2).frame(width: 38)
                    Text(kid.avatar).font(.system(size: 34))
                    VStack(alignment: .leading) {
                        Text(kid.name).font(.system(.title3, design: .rounded).bold())
                        Text("Level \(kid.level) • 🔥 \(kid.streakDays)").font(.caption).foregroundStyle(.secondary)
                    }
                    Spacer()
                    Text("\(kid.totalXP) XP").font(.headline)
                }
                .listRowBackground(kid.id == store.currentID ? KidTheme.yellow.opacity(0.25) : nil)
            }
        }
        .navigationTitle("🏆 Leaderboard")
    }

    private func medal(_ i: Int) -> String {
        switch i { case 0: return "🥇"; case 1: return "🥈"; case 2: return "🥉"; default: return "\(i + 1)" }
    }
}
