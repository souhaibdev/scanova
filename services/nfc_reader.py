import logging
import threading
import time
from typing import Callable, Optional

from pynput import keyboard

logger = logging.getLogger(__name__)


class NFCReader:
    """
    Real-time NFC/RFID reader using pynput global keyboard listener.
    The reader operates in HID keyboard mode: the NFC device types the UID
    followed by ENTER. This class captures that input globally.
    """

    def __init__(self, on_scan_callback: Callable[[str], None]):
        self._callback = on_scan_callback
        self._buffer: list[str] = []
        self._lock = threading.Lock()
        self._last_scan_time: float = 0
        self._debounce_seconds: float = 2.5
        self._listener: Optional[keyboard.Listener] = None
        self._running = False
        self.last_activity_time: float = 0

    def start(self):
        """Start the global keyboard listener in a daemon thread."""
        if self._running:
            return
        self._running = True
        self._listener = keyboard.Listener(
            on_press=self._on_key_press,
            daemon=True,
        )
        self._listener.start()
        logger.info("NFC Reader (HID listener) started.")

    def stop(self):
        """Stop the listener."""
        self._running = False
        if self._listener:
            self._listener.stop()
            self._listener = None
        logger.info("NFC Reader (HID listener) stopped.")

    def _on_key_press(self, key):
        """Handle each key press event."""
        try:
            if key == keyboard.Key.enter:
                self._process_buffer()
            elif hasattr(key, "char") and key.char is not None:
                with self._lock:
                    self._buffer.append(key.char)
        except Exception:
            logger.exception("Error in NFC key handler")

    def _process_buffer(self):
        """Called when ENTER is pressed — treat buffer contents as UID."""
        with self._lock:
            uid = "".join(self._buffer).strip()
            self._buffer.clear()

        # Validate UID before processing
        if not uid:
            logger.debug("Empty UID scanned, ignoring")
            return

        # Check for obviously invalid UIDs (too long, contains invalid chars, etc.)
        if len(uid) > 50:  # Reasonable max length for UID
            logger.warning("Invalid UID scanned (too long): %s", uid[:100])  # Truncate for logging
            return

        # Check for non-alphanumeric characters (UIDs should typically be alphanumeric)
        if not uid.replace('-', '').replace('_', '').isalnum():
            logger.warning("Invalid UID scanned (contains invalid characters): %s", uid)
            return

        # Check for obviously fake/invalid UIDs
        invalid_patterns = ['test', 'fake', 'invalid', 'null', 'none', 'walakinmateafichaliwalo']
        uid_lower = uid.lower()
        for pattern in invalid_patterns:
            if pattern in uid_lower:
                logger.warning("Invalid UID pattern detected: %s", uid)
                return

        now = time.time()
        # Debounce: ignore duplicate scans within threshold
        if (now - self._last_scan_time) < self._debounce_seconds:
            logger.debug("Debounce: ignoring duplicate scan of %s", uid)
            return

        self._last_scan_time = now
        self.last_activity_time = now
        logger.info("Valid NFC UID captured: %s", uid)

        # Fire callback in a separate thread to avoid blocking the listener
        threading.Thread(target=self._callback, args=(uid,), daemon=True).start()

    def is_connected_hint(self) -> bool:
        """Logical connection hint based on recent activity."""
        return (time.time() - self.last_activity_time) < 30
