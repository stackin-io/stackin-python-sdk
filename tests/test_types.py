import unittest

from stackin import DocumentType, Environment


class TestTypes(unittest.TestCase):
    def test_document_type_values(self):
        self.assertEqual(DocumentType.NFE.value, "nfe")
        self.assertEqual(DocumentType.NFSE.value, "nfse")

    def test_environment_values(self):
        self.assertEqual(Environment.LOCAL.value, "local")
        self.assertEqual(Environment.TEST.value, "test")
        self.assertEqual(Environment.PRODUCTION.value, "production")


if __name__ == "__main__":
    unittest.main()
