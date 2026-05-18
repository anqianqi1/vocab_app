import Foundation
import GRDB
import VocabularyContent

public protocol LessonRepository {
    func lessons() async throws -> [Lesson]
    func lesson(withID id: String) async throws -> Lesson?
}

public protocol EntryRepository {
    func entries(forLesson lessonID: String) async throws -> [VocabularyEntry]
    func search(term: String) async throws -> [VocabularyEntry]
}

public final class SQLiteDataStore: LessonRepository, EntryRepository {
    private let dbQueue: DatabaseQueue

    public init(databaseURL: URL) throws {
        self.dbQueue = try DatabaseQueue(path: databaseURL.path)
    }

    public func lessons() async throws -> [Lesson] {
        try await dbQueue.read { db in
            // TODO: replace with joined query once lesson materialized view exists.
            let rows = try Row.fetchAll(db, sql: """
                SELECT section AS section,
                       source_id AS sourceID,
                       COUNT(*) AS entryCount
                FROM entries
                GROUP BY source_id, section
                ORDER BY source_id, section
            """)
            return rows.enumerated().map { index, row in
                let section: String = row["section"] ?? ""
                let sourceID: String = row["sourceID"]
                let entryCount: Int = row["entryCount"]
                return Lesson(
                    id: "\(sourceID)-\(section)",
                    title: section.isEmpty ? "Section \(index + 1)" : section,
                    section: section,
                    sourceID: sourceID,
                    entryCount: entryCount
                )
            }
        }
    }

    public func lesson(withID id: String) async throws -> Lesson? {
        let lessons = try await lessons()
        return lessons.first { $0.id == id }
    }

    public func entries(forLesson lessonID: String) async throws -> [VocabularyEntry] {
        try await dbQueue.read { db in
            let components = lessonID.split(separator: "-")
            guard components.count >= 2 else { return [] }
            let sourceID = components.dropLast().joined(separator: "-")
            let section = components.last.map(String.init)

            let sql = """
                SELECT * FROM entries
                WHERE source_id = ? AND section = ?
                ORDER BY source_page, source_order
            """
            let rows = try Row.fetchAll(db, sql: sql, arguments: [sourceID, section ?? ""])
            return rows.map(Self.makeVocabularyEntry)
        }
    }

    public func search(term: String) async throws -> [VocabularyEntry] {
        try await dbQueue.read { db in
            let sql = """
                SELECT e.* FROM entries e
                JOIN entries_fts fts ON fts.rowid = e.rowid
                WHERE entries_fts MATCH ?
                ORDER BY rank
                LIMIT 25
            """
            let rows = try Row.fetchAll(db, sql: sql, arguments: [term + "*"])
            return rows.map(Self.makeVocabularyEntry)
        }
    }

    private static func makeVocabularyEntry(from row: Row) -> VocabularyEntry {
        let related: [String] = (row["related_terms_json"] as String?)
            .flatMap { try? JSONDecoder().decode([String].self, from: Data($0.utf8)) } ?? []
        let warnings: [String] = (row["warnings_json"] as String?)
            .flatMap { try? JSONDecoder().decode([String].self, from: Data($0.utf8)) } ?? []

        return VocabularyEntry(
            id: row["id"],
            term: row["term"],
            definition: row["definition"] ?? "",
            partOfSpeech: row["part_of_speech"],
            example: row["example"],
            section: row["section"],
            category: row["category"] ?? "uncategorized",
            sourceID: row["source_id"],
            relatedTerms: related,
            warnings: warnings
        )
    }
}
