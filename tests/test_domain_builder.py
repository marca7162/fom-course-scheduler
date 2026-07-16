import unittest

from work.scripts.domain_builder import generate_options_for_row


class DomainBuilderTests(unittest.TestCase):
    def test_all_availability_creates_two_day_alternatives(self):
        options = generate_options_for_row({
            "day_group": "ALL",
            "period_options": "1,2,3,4,5,6,7",
            "preference": "none",
            "weekly_meeting": "",
        })

        self.assertTrue(options)
        self.assertTrue(all(len(option) == 2 for option in options))
        self.assertTrue(all({day for day, _ in option} in ({"M", "W"}, {"T", "TH"}) for option in options))
        self.assertTrue(all(len({period for _, period in option}) == 1 for option in options))

    def test_once_weekly_all_availability_creates_one_day_options(self):
        options = generate_options_for_row({
            "day_group": "ALL",
            "period_options": "1,2",
            "preference": "once_per_week",
            "weekly_meeting": "1",
        })

        self.assertEqual(len(options), 8)
        self.assertTrue(all(len(option) == 1 for option in options))

    def test_period_eight_is_only_a_marker(self):
        options = generate_options_for_row({
            "day_group": "MW",
            "period_options": "1,2,8",
            "preference": "required",
            "weekly_meeting": "",
        })

        self.assertTrue(all(period != 8 for option in options for _, period in option))


if __name__ == "__main__":
    unittest.main()
