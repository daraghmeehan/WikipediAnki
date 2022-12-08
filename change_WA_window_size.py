import win32gui # for moving the WA window

# moving WA window to right side of screen
win32gui.MoveWindow(win32gui.GetForegroundWindow(), 1100, 0, 613, 927, True)