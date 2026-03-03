import json
import unittest
from kie_api.results import _extract_result_urls

class TestResults(unittest.TestCase):
    def test_extract_result_urls_success(self):
        record_data = {
            "resultJson": json.dumps({"resultUrls": ["https://example.com/1.jpg", "https://example.com/2.jpg"]})
        }
        expected = ["https://example.com/1.jpg", "https://example.com/2.jpg"]
        self.assertEqual(_extract_result_urls(record_data), expected)

    def test_extract_result_urls_missing_result_json(self):
        record_data = {}
        with self.assertRaisesRegex(RuntimeError, "Task completed without resultJson."):
            _extract_result_urls(record_data)

    def test_extract_result_urls_invalid_json(self):
        record_data = {
            "resultJson": "invalid-json"
        }
        with self.assertRaisesRegex(RuntimeError, "resultJson is not valid JSON."):
            _extract_result_urls(record_data)

    def test_extract_result_urls_missing_result_urls(self):
        record_data = {
            "resultJson": json.dumps({"otherKey": "value"})
        }
        with self.assertRaisesRegex(RuntimeError, "resultJson does not contain resultUrls."):
            _extract_result_urls(record_data)

    def test_extract_result_urls_result_urls_not_list(self):
        record_data = {
            "resultJson": json.dumps({"resultUrls": "not-a-list"})
        }
        with self.assertRaisesRegex(RuntimeError, "resultJson does not contain resultUrls."):
            _extract_result_urls(record_data)

if __name__ == "__main__":
    unittest.main()
