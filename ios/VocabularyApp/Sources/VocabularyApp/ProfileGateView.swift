import SwiftUI
import VocabularyContent
import VocabularyData

struct ProfileGateView: View {
    @Bindable var store: ProfileStore
    @State private var newName = ""
    @State private var avatar = PlayerProfile.avatarChoices[0]

    private var kids: [PlayerProfile] { store.profiles.filter { !$0.isSimulated } }

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                Text("📚").font(.system(size: 80))
                KidTheme.title("Word Heroes")
                Text("Who's learning today?")
                    .font(.system(.title3, design: .rounded)).foregroundStyle(.secondary)

                if !kids.isEmpty {
                    ForEach(kids) { kid in
                        Button { store.select(kid) } label: {
                            HStack(spacing: 14) {
                                Text(kid.avatar).font(.system(size: 40))
                                VStack(alignment: .leading) {
                                    Text(kid.name).font(.system(.title2, design: .rounded).bold())
                                    Text("Level \(kid.level) • \(kid.totalXP) XP")
                                        .font(.subheadline).foregroundStyle(.secondary)
                                }
                                Spacer()
                                Image(systemName: "chevron.right")
                            }
                            .padding().background(.thinMaterial, in: RoundedRectangle(cornerRadius: 18))
                        }.buttonStyle(.plain)
                    }
                }

                VStack(spacing: 14) {
                    Text("New hero").font(.headline)
                    LazyVGrid(columns: Array(repeating: GridItem(), count: 6), spacing: 10) {
                        ForEach(PlayerProfile.avatarChoices, id: \.self) { choice in
                            Text(choice).font(.system(size: 34)).padding(6)
                                .background(avatar == choice ? KidTheme.purple.opacity(0.25) : .clear, in: Circle())
                                .onTapGesture { avatar = choice }
                        }
                    }
                    TextField("Your name", text: $newName)
                        .textFieldStyle(.roundedBorder).font(.title3)
                    Button("Start") {
                        store.addProfile(name: newName.isEmpty ? "Hero" : newName, avatar: avatar)
                    }.buttonStyle(BigButtonStyle(color: KidTheme.green))
                }
                .padding().background(.thinMaterial, in: RoundedRectangle(cornerRadius: 20))
            }
            .padding()
        }
    }
}
