import unittest

from stackin import APIError, ConnectionFailedError, InvoiceError


class TestExceptions(unittest.TestCase):
    def test_invoice_error_is_an_exception(self):
        error = InvoiceError("boom")
        self.assertIsInstance(error, Exception)
        self.assertEqual(str(error), "boom")

    def test_api_error_carries_status_code_and_detail(self):
        error = APIError(status_code=404, detail="not found")
        self.assertEqual(error.status_code, 404)
        self.assertEqual(error.detail, "not found")
        self.assertEqual(str(error), "[404] not found")
        self.assertIsInstance(error, InvoiceError)

    def test_connection_failed_error_is_invoice_error(self):
        error = ConnectionFailedError("could not connect")
        self.assertIsInstance(error, InvoiceError)
        self.assertEqual(str(error), "could not connect")


if __name__ == "__main__":
    unittest.main()
