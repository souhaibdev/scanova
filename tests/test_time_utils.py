import unittest

from utils.time_utils import calc_worked_hours


class TimeUtilsTests(unittest.TestCase):
    def test_calc_worked_hours_rounds_to_45_minute_rule(self):
        cases = [
            ("08:00", "09:00", 1.0),
            ("08:00", "09:20", 1.0),
            ("08:00", "09:44", 1.0),
            ("08:00", "09:45", 2.0),
            ("08:00", "09:59", 2.0),
            ("08:00", "10:10", 2.0),
            ("08:00", "10:44", 2.0),
            ("08:00", "10:45", 3.0),
        ]
        for entry, exit_time, expected in cases:
            with self.subTest(entry=entry, exit_time=exit_time):
                self.assertEqual(calc_worked_hours(entry, exit_time), expected)


if __name__ == "__main__":
    unittest.main()
