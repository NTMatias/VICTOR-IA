from unittest.mock import patch
from PIL import Image
from tests.test_victor import Fixture
from victor.system.screen import ScreenManager
from victor.errors import VictorError


class ScreenTests(Fixture):
    def test_imagegrab_fallback(self):
        with patch("mss.MSS", side_effect=OSError("blocked")), patch("PIL.ImageGrab.grab", return_value=Image.new("RGB", (120, 80))) as fallback:
            result = ScreenManager(self.cfg).capture()
        fallback.assert_called_once()
        self.assertEqual(result["ancho"], 120)

    def test_both_fail_friendly_error(self):
        with patch("mss.MSS", side_effect=OSError("raw driver error")), patch("PIL.ImageGrab.grab", side_effect=OSError("raw driver error")):
            with self.assertRaisesRegex(VictorError, "MSS ni ImageGrab") as error:
                ScreenManager(self.cfg).capture()
        self.assertNotIn("raw driver error", str(error.exception))
