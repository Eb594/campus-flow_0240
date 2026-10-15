import copy
import tempfile
import unittest
from pathlib import Path

from campus_flow.tickets import TicketManager


class SearchFixture(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.manager = TicketManager(Path(self.temp_dir.name) / "t.json")
        m = self.manager
        m.create_ticket("WiFi down in library", "Network", "high", 12)  # T001 critical
        m.create_ticket("Projector broken", "Hardware", "medium", 2)    # T002 medium
        m.create_ticket("wifi slow in lab", "Network", "low", 1)        # T003 low
        m.create_ticket("Install Matlab", "Software", "low", 5)         # T004 medium
        m.assign_ticket("T003", "Ada")
        m.update_status("T003", "in_progress")

    def tearDown(self):
        self.temp_dir.cleanup()

    def ids(self, results):
        return [t["id"] for t in results]


class TestIndividualFilters(SearchFixture):
    def test_title_is_case_insensitive_substring(self):
        self.assertEqual(self.ids(self.manager.search_filtered("WIFI")), ["T001", "T003"])
        self.assertEqual(self.ids(self.manager.search_filtered("  proj ")), ["T002"])

    def test_category_filter(self):
        self.assertEqual(self.ids(self.manager.search_filtered(category="network")), ["T001", "T003"])

    def test_status_filter(self):
        self.assertEqual(self.ids(self.manager.search_filtered(status="in_progress")), ["T003"])

    def test_priority_filter(self):
        self.assertEqual(self.ids(self.manager.search_filtered(priority="medium")), ["T002", "T004"])

    def test_no_match_returns_empty_list(self):
        self.assertEqual(self.manager.search_filtered("nothing like this"), [])


class TestCombinedFilters(SearchFixture):
    def test_all_filters_use_and(self):
        results = self.manager.search_filtered("wifi", "Network", "open", "critical")
        self.assertEqual(self.ids(results), ["T001"])

    def test_one_failing_filter_excludes_ticket(self):
        self.assertEqual(self.manager.search_filtered("wifi", "Network", "resolved"), [])

    def test_category_and_status(self):
        results = self.manager.search_filtered(category="Network", status="open")
        self.assertEqual(self.ids(results), ["T001"])

    def test_empty_filters_do_not_restrict(self):
        results = self.manager.search_filtered("", "", "  ", None)
        self.assertEqual(len(results), 4)


class TestInvalidFilters(SearchFixture):
    def test_invalid_values_raise(self):
        with self.assertRaises(ValueError):
            self.manager.search_filtered(category="Furniture")
        with self.assertRaises(ValueError):
            self.manager.search_filtered(status="done")
        with self.assertRaises(ValueError):
            self.manager.search_filtered(priority="urgent")

    def test_invalid_filters_do_not_modify_tickets(self):
        before = copy.deepcopy(self.manager.tickets)
        with self.assertRaises(ValueError):
            self.manager.search_filtered("wifi", status="bogus")
        self.assertEqual(self.manager.tickets, before)


class TestReadOnly(SearchFixture):
    def test_search_does_not_change_tickets_or_queue(self):
        before = copy.deepcopy(self.manager.tickets)
        queue_before = copy.deepcopy(self.manager.get_work_queue())

        results = self.manager.search_filtered("wifi")
        results[0]["status"] = "resolved"          # mutate the returned copy
        self.manager.sort_by_priority(results)

        self.assertEqual(self.manager.tickets, before)
        self.assertEqual(self.manager.get_work_queue(), queue_before)

    def test_search_does_not_write_to_disk(self):
        path = self.manager.file_path
        before = path.read_text()
        self.manager.search_filtered("wifi", "Network")
        self.assertEqual(path.read_text(), before)


class TestPrioritySortedView(SearchFixture):
    def test_sorted_view_orders_by_priority_then_id(self):
        results = self.manager.search_filtered()
        self.assertEqual(self.ids(self.manager.sort_by_priority(results)),
                         ["T001", "T002", "T004", "T003"])

    def test_sorted_view_does_not_reorder_input(self):
        results = self.manager.search_filtered()
        original = self.ids(results)
        self.manager.sort_by_priority(results)
        self.assertEqual(self.ids(results), original)


if __name__ == "__main__":
    unittest.main()