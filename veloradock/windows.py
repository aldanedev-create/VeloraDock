"""Small Windows adapters. No global keyboard hooks or silent script execution."""
import ctypes
from ctypes import wintypes
import os
import threading
import time


def clipboard_text():
    user, kernel = ctypes.windll.user32, ctypes.windll.kernel32
    user.GetClipboardData.restype = ctypes.c_void_p
    kernel.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel.GlobalLock.restype = ctypes.c_void_p
    kernel.GlobalUnlock.argtypes = [ctypes.c_void_p]
    if not user.OpenClipboard(None):
        return ''
    try:
        handle = user.GetClipboardData(13)
        pointer = kernel.GlobalLock(handle) if handle else None
        if not pointer:
            return ''
        try:
            return ctypes.wstring_at(pointer)[:10001]
        finally:
            kernel.GlobalUnlock(handle)
    finally:
        user.CloseClipboard()


def copy_text(text):
    if os.name != 'nt':
        raise RuntimeError('Native clipboard requires Windows')
    user, kernel = ctypes.windll.user32, ctypes.windll.kernel32
    kernel.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel.GlobalAlloc.restype = ctypes.c_void_p
    kernel.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel.GlobalLock.restype = ctypes.c_void_p
    kernel.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel.GlobalFree.argtypes = [ctypes.c_void_p]
    user.SetClipboardData.argtypes = [wintypes.UINT, ctypes.c_void_p]
    user.SetClipboardData.restype = ctypes.c_void_p
    encoded = (text + '\0').encode('utf-16-le')
    handle = kernel.GlobalAlloc(0x42, len(encoded))
    if not handle:
        raise ctypes.WinError()
    pointer = kernel.GlobalLock(handle)
    if not pointer:
        kernel.GlobalFree(handle)
        raise ctypes.WinError()
    ctypes.memmove(pointer, encoded, len(encoded))
    kernel.GlobalUnlock(handle)
    if not user.OpenClipboard(None):
        kernel.GlobalFree(handle)
        raise RuntimeError('Clipboard is busy; try again')
    try:
        user.EmptyClipboard()
        if not user.SetClipboardData(13, handle):
            kernel.GlobalFree(handle)
            raise ctypes.WinError()
    finally:
        user.CloseClipboard()

class WindowsServices:
    def __init__(self, app, show):
        self._app = app
        self._show = show
        self._stop = threading.Event()
        self._thread_id = None
        self.hotkey_error = ''

    def start(self):
        if os.name != 'nt':
            return
        threading.Thread(target=self._hotkeys, daemon=True).start()
        threading.Thread(target=self._clipboard, daemon=True).start()

    def _hotkeys(self):
        user = ctypes.windll.user32
        self._thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
        # MOD_NOREPEAT | CONTROL | ALT; user can choose among three conflict-safe alternatives.
        keys = {'Ctrl+Alt+Space': (0x4003, 0x20), 'Ctrl+Shift+Space': (0x4006, 0x20), 'Alt+Space': (0x4001, 0x20)}
        selected = self._app.store.setting('hotkey', 'Ctrl+Alt+Space')
        modifiers, key = keys.get(selected, keys['Ctrl+Alt+Space'])
        if not user.RegisterHotKey(None, 1, modifiers, key):
            self.hotkey_error = 'Hotkey is in use. Choose another shortcut in Settings and restart.'
            return
        message = wintypes.MSG()
        try:
            while user.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
                if message.message == 0x312:
                    self._show()
        finally:
            user.UnregisterHotKey(None, 1)

    def _clipboard(self):
        last = 0
        user = ctypes.windll.user32
        while not self._stop.wait(.75):
            # Do not read clipboard content while collection is paused.
            if not self._app.store.setting('clipboard_enabled', False):
                continue
            sequence = user.GetClipboardSequenceNumber()
            if sequence != last:
                last = sequence
                try:
                    self._app.clipboard.capture(clipboard_text())
                except (OSError, RuntimeError):
                    pass

    def stop(self):
        self._stop.set()
        if self._thread_id:
            ctypes.windll.user32.PostThreadMessageW(self._thread_id, 0x12, 0, 0)
