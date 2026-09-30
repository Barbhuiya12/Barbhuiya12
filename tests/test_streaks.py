import datetime
import unittest
from scripts.update_activity import streaks


class StreakTests(unittest.TestCase):
    today = datetime.date(2026, 10, 1)

    def calendar(self, counts):
        start = self.today - datetime.timedelta(days=len(counts) - 1)
        return {"weeks": [{"contributionDays": [{"date": (start + datetime.timedelta(days=i)).isoformat(), "contributionCount": count} for i, count in enumerate(counts)]}]}

    def test_today_active(self):
        self.assertEqual(streaks(self.calendar([0, 2, 1, 3]), self.today), (3, 3, 3))

    def test_today_incomplete(self):
        self.assertEqual(streaks(self.calendar([0, 2, 1, 0]), self.today), (2, 2, 2))

    def test_streak_broken_yesterday(self):
        self.assertEqual(streaks(self.calendar([2, 1, 0, 0]), self.today), (0, 2, 2))

    def test_longest_distinct_from_current(self):
        self.assertEqual(streaks(self.calendar([1, 1, 1, 0, 1]), self.today), (1, 3, 4))

    def test_empty_calendar(self):
        self.assertEqual(streaks({"weeks": []}, self.today), (0, 0, 0))


if __name__ == "__main__":
    unittest.main()
