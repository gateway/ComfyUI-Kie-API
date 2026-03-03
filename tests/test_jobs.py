import unittest
from kie_api.jobs import _should_retry_fail


class TestShouldRetryFail(unittest.TestCase):
    def test_5xx_status_codes(self):
        # Test integer 5xx codes
        self.assertTrue(_should_retry_fail(500, None, None))
        self.assertTrue(_should_retry_fail(502, None, None))
        self.assertTrue(_should_retry_fail(599, None, None))

        # Test string 5xx codes
        self.assertTrue(_should_retry_fail("500", None, None))
        self.assertTrue(_should_retry_fail("503", None, None))
        self.assertTrue(_should_retry_fail("599", None, None))

    def test_non_5xx_status_codes(self):
        # Test integer non-5xx codes
        self.assertFalse(_should_retry_fail(400, None, None))
        self.assertFalse(_should_retry_fail(404, None, None))
        self.assertFalse(_should_retry_fail(200, None, None))
        self.assertFalse(_should_retry_fail(100, None, None))
        self.assertFalse(_should_retry_fail(600, None, None))

        # Test string non-5xx codes
        self.assertFalse(_should_retry_fail("400", None, None))
        self.assertFalse(_should_retry_fail("403", None, None))

    def test_transient_messages(self):
        # Test "internal error"
        self.assertTrue(_should_retry_fail(None, "internal error", None))
        self.assertTrue(_should_retry_fail(None, None, "An Internal Error occurred"))
        self.assertTrue(_should_retry_fail(None, "internal error something", "else"))

        # Test "try again later"
        self.assertTrue(_should_retry_fail(None, "try again later", None))
        self.assertTrue(_should_retry_fail(None, None, "Please try again later."))

        # Test combined texts
        self.assertTrue(_should_retry_fail(None, "please try", "again later"))
        self.assertTrue(_should_retry_fail(None, "internal", "error"))

    def test_non_transient_messages(self):
        self.assertFalse(_should_retry_fail(None, "bad request", None))
        self.assertFalse(_should_retry_fail(None, None, "invalid parameters"))
        self.assertFalse(_should_retry_fail(None, "unauthorized", "access denied"))

    def test_edge_cases(self):
        # None values
        self.assertFalse(_should_retry_fail(None, None, None))

        # Invalid string for code
        self.assertFalse(_should_retry_fail("not_an_int", None, None))

        # Wrong types for message
        self.assertFalse(_should_retry_fail(None, ["internal", "error"], None))
        self.assertFalse(_should_retry_fail(None, None, {"error": "internal error"}))

        # Check if code triggers true despite non-transient message
        self.assertTrue(_should_retry_fail(500, "bad request", "invalid"))

        # Check if message triggers true despite non-5xx code
        self.assertTrue(_should_retry_fail(400, "internal error", None))


if __name__ == '__main__':
    unittest.main()
