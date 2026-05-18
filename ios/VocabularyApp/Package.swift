// swift-tools-version: 5.9
import PackageDescription
let package = Package(
    name: "VocabularyApp",
    platforms: [
        .iOS(.v17),
        .macOS(.v14)
    ],
    products: [
        .library(name: "VocabularyContent", targets: ["VocabularyContent"]),
        .library(name: "VocabularyData", targets: ["VocabularyData"]),
        .library(name: "VocabularyFeatures", targets: ["VocabularyFeatures"]),
        .executable(name: "VocabularyApp", targets: ["VocabularyApp"])
    ],
    dependencies: [
        .package(url: "https://github.com/groue/GRDB.swift", from: "6.0.0")
    ],
    targets: [
        .target(
            name: "VocabularyContent",
            dependencies: [],
            path: "Sources/VocabularyContent"
        ),
        .target(
            name: "VocabularyData",
            dependencies: [
                "VocabularyContent",
                .product(name: "GRDB", package: "GRDB.swift")
            ],
            path: "Sources/VocabularyData"
        ),
        .target(
            name: "VocabularyFeatures",
            dependencies: [
                "VocabularyContent",
                "VocabularyData"
            ],
            path: "Sources/VocabularyFeatures"
        ),
        .executableTarget(
            name: "VocabularyApp",
            dependencies: [
                "VocabularyContent",
                "VocabularyData",
                "VocabularyFeatures"
            ],
            path: "Sources/VocabularyApp",
            resources: [
                .process("Resources")
            ],
            linkerSettings: [
                .unsafeFlags([
                    "-sectcreate",
                    "__TEXT",
                    "__info_plist",
                    "Sources/VocabularyApp/AppInfo.plist"
                ], .when(platforms: [.iOS]))
            ]
        ),
        .testTarget(
            name: "VocabularyAppTests",
            dependencies: ["VocabularyData", "VocabularyFeatures"],
            path: "Tests/VocabularyAppTests"
        )
    ]
)
