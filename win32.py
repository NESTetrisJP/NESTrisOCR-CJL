# Almost a duplicate of NESTrisOCR
import win32ui
import win32gui
import win32process
import win32con
import pywintypes
from PIL import Image

'''
copied from http://nullege.com/codes/show/src@w@a@wallmanager-HEAD@mtmenu@window_manager.py/70/win32gui.EnumWindows
'''
def isRealWindow(hWnd):
  '''Return True iff given handler corespond to a real visible window on the desktop.'''
  if not win32gui.IsWindowVisible(hWnd):
    return False
  if win32gui.GetParent(hWnd) != 0:
    return False
  hasNoOwner = win32gui.GetWindow(hWnd, win32con.GW_OWNER) == 0
  lExStyle = win32gui.GetWindowLong(hWnd, win32con.GWL_EXSTYLE)
  if (((lExStyle & win32con.WS_EX_TOOLWINDOW) == 0 and hasNoOwner)
      or ((lExStyle & win32con.WS_EX_APPWINDOW != 0) and not hasNoOwner)):
    if win32gui.GetWindowText(hWnd):
      return True
  return False

def checkWindow(hwnd):
  '''checks if a window still exists'''
  return hwnd if win32gui.IsWindow(hwnd) else None

def getWindows():
  '''
  Return a list of tuples (handler, (width, height)) for each real window.
  '''
  def callback(hWnd, windows):
    if not isRealWindow(hWnd):
      return
    text = win32gui.GetWindowText(hWnd)
    windows.append((hWnd, text))
  windows = []
  win32gui.EnumWindows(callback, windows)
  return windows

class Win32UICapture(object):
  def __init__(self):
    self.lastRectangle = None
    self.lasthwndTarget = None
    self.hDC = None
    self.myDC = None
    self.newDC = None
    self.myBitMap = None

  def initAll(self):
    hwnd = self.lasthwndTarget
    x, y, w, h = self.lastRectangle
    self.hDC = win32gui.GetDC(hwnd)
    self.myDC = win32ui.CreateDCFromHandle(self.hDC)
    self.newDC = self.myDC.CreateCompatibleDC()

    self.myBitMap = win32ui.CreateBitmap()
    self.myBitMap.CreateCompatibleBitmap(self.myDC, w, h)

    self.newDC.SelectObject(self.myBitMap)

  def releaseAll(self):
    hwnd = self.lasthwndTarget
    if self.myDC is not None:
      try:
        self.myDC.DeleteDC()
      except win32ui.error:
        pass
      finally:
        self.myDC = None

    if self.newDC is not None:
      try:
        self.newDC.DeleteDC()
      except win32ui.error:
        pass
      finally:
        self.newDC = None

    if self.hDC is not None:
      win32gui.ReleaseDC(hwnd, self.hDC)
      self.hDC = None

    if self.myBitMap is not None:
      win32gui.DeleteObject(self.myBitMap.GetHandle())
      self.myBitMap = None

  def capture(self, rectangle, hwndTarget):
    x, y, w, h = rectangle
    hwnd = hwndTarget
    if w <= 0 or h <= 0 or hwnd == 0:
      return None

    try:
      if self.lastRectangle != rectangle or self.lasthwndTarget != hwndTarget:
        self.releaseAll()
        self.lastRectangle = rectangle
        self.lasthwndTarget = hwndTarget
        self.initAll()

      self.newDC.BitBlt((0, 0), (w, h) , self.myDC, (x, y), win32con.SRCCOPY)
      self.myBitMap.Paint(self.newDC)
      bmpinfo = self.myBitMap.GetInfo()
      bmpstr = self.myBitMap.GetBitmapBits(True)
      im = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
      # Free Resources
      return im
    except pywintypes.error:
      raise
    except win32ui.error:
      raise
    return None