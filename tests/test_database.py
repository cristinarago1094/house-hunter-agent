import tempfile
import unittest
from pathlib import Path

from services.database import connect, reset_database


class DatabaseTest(unittest.TestCase):
    def test_reset_database_removes_local_sqlite_file(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "house_hunter.db"
            connection = connect(database_path)
            connection.close()

            removed = reset_database(database_path)

            self.assertTrue(removed)
            self.assertFalse(database_path.exists())


if __name__ == "__main__":
    unittest.main()
