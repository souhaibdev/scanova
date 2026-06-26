import unittest
from unittest.mock import patch

from services import license_service


class LicenseServiceTests(unittest.TestCase):
    def setUp(self):
        self.storage = {}

        self.load_patch = patch(
            "services.license_service.load_json",
            side_effect=lambda filename: dict(self.storage),
        )
        self.save_patch = patch(
            "services.license_service.save_json",
            side_effect=self._save_activation,
        )
        self.load_patch.start()
        self.save_patch.start()
        self.addCleanup(self.load_patch.stop)
        self.addCleanup(self.save_patch.stop)

    def _save_activation(self, filename, data):
        self.storage.clear()
        self.storage.update(data)

    def test_activate_with_valid_code(self):
        ok, msg = license_service.activate("wrong-code")
        self.assertFalse(ok)
        self.assertFalse(license_service.is_activated())

        ok, msg = license_service.activate(license_service.ACTIVATION_CODE)
        self.assertTrue(ok)
        self.assertTrue(license_service.is_activated())


if __name__ == "__main__":
    unittest.main()
