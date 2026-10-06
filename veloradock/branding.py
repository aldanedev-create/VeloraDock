"""Apply the packaged icon to the native window without a .NET dependency."""
import ctypes
import os
from pathlib import Path


def set_window_icon(title: str):
    if os.name != 'nt':
        return None
    user = ctypes.windll.user32
    user.FindWindowW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
    user.FindWindowW.restype = ctypes.c_void_p
    user.LoadImageW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
    user.LoadImageW.restype = ctypes.c_void_p
    user.SendMessageW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_size_t, ctypes.c_ssize_t]
    user.SendMessageW.restype = ctypes.c_ssize_t
    icon = user.LoadImageW(None, str(Path(__file__).parent / 'public' / 'app.ico'), 1, 0, 0, 0x10)
    window = user.FindWindowW(None, title)
    if window and icon:
        user.SendMessageW(window, 0x80, 0, icon)
        user.SendMessageW(window, 0x80, 1, icon)
    return icon


def release_icon(icon):
    if os.name == 'nt' and icon:
        ctypes.windll.user32.DestroyIcon.argtypes = [ctypes.c_void_p]
        ctypes.windll.user32.DestroyIcon(icon)
