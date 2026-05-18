import XCTest
@testable import VocabularyData

final class RepositoryTests: XCTestCase {
    func testDatabaseInitializationFailsWithMissingFile() {
        XCTAssertThrowsError(try SQLiteDataStore(databaseURL: URL(fileURLWithPath: "/path/does/not/exist")))
    }
}
