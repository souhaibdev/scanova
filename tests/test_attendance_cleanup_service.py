import unittest
from datetime import date

from services.attendance_cleanup_service import should_keep_month


class AttendanceCleanupServiceTests(unittest.TestCase):
    def test_should_keep_current_and_previous_months_only(self):
        current = date(2026, 6, 15)
        self.assertTrue(should_keep_month("2026-06", current))
        self.assertTrue(should_keep_month("2026-05", current))
        self.assertFalse(should_keep_month("2026-04", current))
        self.assertFalse(should_keep_month("2025-12", current))

    def test_should_handle_year_transition(self):
        current = date(2026, 1, 10)
        self.assertTrue(should_keep_month("2026-01", current))
        self.assertTrue(should_keep_month("2025-12", current))
        self.assertFalse(should_keep_month("2025-11", current))


if __name__ == "__main__":
    unittest.main()
