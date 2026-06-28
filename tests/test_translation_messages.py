import unittest

from services import auth_service
from translation_manager import TranslationManager


class TranslationMessagesTests(unittest.TestCase):
    def setUp(self):
        self.translator = TranslationManager.instance()
        self.translator.set_language("en")

    def test_auth_service_messages_follow_current_language(self):
        self.translator.set_language("ar")

        ok, msg = auth_service.register_admin("", "")

        self.assertFalse(ok)
        self.assertEqual(msg, self.translator.t("auth.validation.username_password_required"))


if __name__ == "__main__":
    unittest.main()
