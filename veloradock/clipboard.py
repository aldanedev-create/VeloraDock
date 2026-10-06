"""Opt-in text history, protected with Windows DPAPI for the current account."""
import ctypes
import hashlib
import os
import time

class Blob(ctypes.Structure):
    _fields_ = [('size', ctypes.c_ulong), ('data', ctypes.POINTER(ctypes.c_ubyte))]

def protect(data: bytes, decrypt=False):
    if os.name != 'nt':
        raise RuntimeError("Clipboard history encryption requires Windows")
    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    destination = Blob()
    ctypes.windll.kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    ctypes.windll.kernel32.LocalFree.restype = ctypes.c_void_p
    function = ctypes.windll.crypt32.CryptUnprotectData if decrypt else ctypes.windll.crypt32.CryptProtectData
    if not function(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(destination)):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(destination.data, destination.size)
    finally:
        ctypes.windll.kernel32.LocalFree(destination.data)

class Clipboard:
    def __init__(self, store):
        self.store = store

    def capture(self, text: str):
        if not self.store.setting('clipboard_enabled', False) or not text or len(text) > 10000:
            return
        self.prune()
        digest = hashlib.sha256(text.encode()).hexdigest()
        latest = self.store.rows('SELECT digest FROM clips ORDER BY id DESC LIMIT 1')
        if latest and latest[0]['digest'] == digest:
            return
        self.store.execute('INSERT INTO clips(data,digest,created) VALUES (?,?,?)',
                           (protect(text.encode()), digest, time.time()))
        self.store.execute('DELETE FROM clips WHERE favorite=0 AND id NOT IN (SELECT id FROM clips ORDER BY id DESC LIMIT 200)')

    def prune(self):
        days = self.store.setting('clipboard_days', 7)
        self.store.execute('DELETE FROM clips WHERE favorite=0 AND created<?', (time.time() - days * 86400,))

    def list(self):
        self.prune()
        result = []
        for row in self.store.rows('SELECT * FROM clips ORDER BY favorite DESC,id DESC LIMIT 200'):
            try:
                row['text'] = protect(row.pop('data'), decrypt=True).decode()
                row.pop('digest')
                result.append(row)
            except (OSError, RuntimeError, UnicodeError):
                continue
        return result

    def clear(self):
        self.store.execute('DELETE FROM clips')
