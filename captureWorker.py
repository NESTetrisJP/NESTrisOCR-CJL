from PyQt5.QtCore import QThread, pyqtSignal
import win32
from PIL import Image
from numba import jit, njit
import numpy as np
import time

SLEEP_TIME = 0.002

class CaptureWorker(QThread):
  done = pyqtSignal(object)

  def __init__(self, parent):
    super().__init__(parent)
    self.exiting = False

    self.captureRate = 1.0 / parent.config.captureFPS
    self.startTime = None
    self.lastCapturedTime = None
    self.capturedFrames = 0
    self.showFPS = 0
    self.lastFPSQueueTime = None
    self.capturedFramesForFPS = 0

    self.capture = win32.Win32UICapture()

    self.inGameChecker = InGameChecker()
    self.fieldReader = FieldReader()
    self.scoreReader = ScoreReader()
    self.linesReader = LinesReader()
    self.levelReader = LevelReader()
    self.nextReader = NextReader()
    self.statsReader = StatsReader()

  def run(self):
    self.startTime = time.time()
    self.lastCapturedTime = self.startTime
    self.lastFPSQueueTime = self.startTime
    while not self.exiting:
      currentTime = time.time()
      if currentTime - self.lastFPSQueueTime > 1:
        self.showFPS = self.capturedFramesForFPS / (currentTime - self.lastFPSQueueTime)
        self.capturedFramesForFPS = 0
        self.lastFPSQueueTime = currentTime

      if currentTime - self.lastCapturedTime > self.captureRate:
        while self.lastCapturedTime + self.captureRate < currentTime:
          self.lastCapturedTime += self.captureRate

        handle = self.parent().currentHandle
        config = self.parent().config
        self.captureRate = 1.0 / config.captureFPS
        self.nextReader.setBlackThreshold(config.blackThreshold)
        self.inGameChecker.setThreshold(config.inGameThreshold)
        try:
          image = self.capture.capture((config.xCoord, config.yCoord, config.width, config.height), handle)
          image = image.resize((512, 448))
          smallImage = image.resize((32, 28))
          inGame = self.inGameChecker.check(smallImage)
          if inGame:
            field = self.fieldReader.read(image)
            score = self.scoreReader.read(image)
            lines = self.linesReader.read(image)
            level = self.levelReader.read(image)
            next_ = self.nextReader.read(image)
            stats = self.statsReader.read(image)
            self.done.emit({ "success": True, "inGame": True, "time": time.time_ns() // 1000000, "field": field, "score": score, "lines": lines, "level": level, "next": next_, "stats": stats, "image": image, "fps": self.showFPS })
          else:
            self.done.emit({ "success": True, "inGame": False, "image": image, "fps": self.showFPS })
        except:
          self.done.emit({ "success": False })
        self.capturedFrames += 1
        self.capturedFramesForFPS += 1

      else:
        self.scoreReader.reset()
        time.sleep(SLEEP_TIME)

SCORE_TILE_X = 24
SCORE_TILE_Y = 7
class ScoreReader:
  def __init__(self):
    self.digitReader = DigitReader()
    self.enableHexRead = False

  def read(self, image):
    result = 0
    for i in range(6):
      x = (SCORE_TILE_X + i) * 16
      y = SCORE_TILE_Y * 16
      d = self.digitReader.read(image.crop((x, y, x + 14, y + 14)), i == 0, False)
      if d[0][0] == -1: break
      if i == 0:
        # Avoid misread '8' to 'B'
        if d[0][0] == 10: self.enableHexRead = True
        if (not self.enableHexRead) and d[0][0] == 11: d[0][0] = 8
      result += d[0][0] * (10 ** (5 - i))
    return result

  def reset(self):
    self.enableHexRead = False

LINES_TILE_X = 19
LINES_TILE_Y = 2
class LinesReader:
  def __init__(self):
    self.digitReader = DigitReader()

  def read(self, image):
    result = 0
    for i in range(3):
      x = (LINES_TILE_X + i) * 16
      y = LINES_TILE_Y * 16
      d = self.digitReader.read(image.crop((x, y, x + 14, y + 14)), False, False)
      if d[0][0] == -1: break
      result += d[0][0] * (10 ** (2 - i))
    return result

LEVEL_TILE_X = 26
LEVEL_TILE_Y = 20
class LevelReader:
  def __init__(self):
    self.digitReader = DigitReader()

  def read(self, image):
    result = 0
    for i in range(2):
      x = (LEVEL_TILE_X + i) * 16
      y = LEVEL_TILE_Y * 16
      d = self.digitReader.read(image.crop((x, y, x + 14, y + 14)), False, False)
      if d[0][0] == -1: break
      result += d[0][0] * (10 ** (1 - i))
    return result

STATS_TILE_X = 6
STATS_TILE_Y = 11
class StatsReader:
  def __init__(self):
    self.digitReader = DigitReader()

  def read(self, image):
    result = [0, 0, 0, 0, 0, 0, 0]
    for i in range(7):
      for j in range(3):
        x = (STATS_TILE_X + j) * 16
        y = (STATS_TILE_Y + i * 2) * 16
        d = self.digitReader.read(image.crop((x, y, x + 14, y + 14)), False, True)
        if d[0][0] == -1: break
        result[i] += d[0][0] * (10 ** (2 - j))
    return result

FIELD_TILE_X = 12
FIELD_TILE_Y = 5

@njit("uint8[:,:](float32[:,:,:],float32[:],float32[:],float32[:],float32[:])")
def readFieldJit(smallImage, blackSample, whiteSample, color1Sample, color2Sample):
  samples = [blackSample, whiteSample, color1Sample, color2Sample]
  # result = [[0] * 10] * 20
  result = np.zeros((20,10), dtype=np.uint8)
  for iy in range(20):
    for ix in range(10):
      x = ix * 4 + 1
      y = iy * 4 + 1
      color = smallImage[y][x]
      closest = 0
      lowest_dist = (256*256)*3
      i = 0
      for i in range(4):
        sample = samples[i]
        dist = ((color[0] - sample[0]) * (color[0] - sample[0]) +
                (color[1] - sample[1]) * (color[1] - sample[1]) +
                (color[2] - sample[2]) * (color[2] - sample[2]))
        if dist < lowest_dist:
          lowest_dist = dist
          closest = i
      result[iy][ix] = closest

  return result

# Not Used
def readFieldSlow(image, blackSample, whiteSample, color1Sample, color2Sample):
  samples = [blackSample, whiteSample, color1Sample, color2Sample]
  result = [[None for _ in range(10)] for _ in range(20)]
  for iy in range(20):
    for ix in range(10):
      x = (FIELD_TILE_X + ix) * 16
      y = (FIELD_TILE_Y + iy) * 16
      color = np.mean(np.asarray(image.crop((x + 5, y + 5, x + 9, y + 9))), (0, 1), dtype=np.float32)
      closest = 0
      lowest_dist = (256*256)*3
      i = 0
      for i in range(4):
        sample = samples[i]
        dist = ((color[0] - sample[0]) * (color[0] - sample[0]) +
                (color[1] - sample[1]) * (color[1] - sample[1]) +
                (color[2] - sample[2]) * (color[2] - sample[2]))
        if dist < lowest_dist:
          lowest_dist = dist
          closest = i
      result[iy][ix] = closest

    return result

class FieldReader:
  def __init__(self):
    pass

  def read(self, image):
    blackSample  = np.mean(np.asarray(image.crop((67, 147, 71, 151))), (0, 1), dtype=np.float32)
    whiteSample  = np.mean(np.asarray(image.crop((67, 173, 71, 177))), (0, 1), dtype=np.float32)
    color1Sample = np.mean(np.asarray(image.crop((69, 205, 73, 208))), (0, 1), dtype=np.float32)
    color2Sample = np.mean(np.asarray(image.crop((69, 239, 73, 243))), (0, 1), dtype=np.float32)

    smallImage = np.asarray(image.crop((FIELD_TILE_X * 16, FIELD_TILE_Y * 16, (FIELD_TILE_X + 10) * 16, (FIELD_TILE_Y + 20) * 16)).resize((40, 80), Image.BILINEAR), dtype=np.float32)
    return readFieldJit(smallImage, blackSample, whiteSample, color1Sample, color2Sample)

class NextReader:
  # orange-red-pink
  bitToPiece = ["I", "J", "T", "Z", "L", "", "S", "O"]
  def __init__(self):
    self.threshold = 25

  def setBlackThreshold(self, threshold):
    self.threshold = threshold

  def isNotBlack(self, color):
    return color[0] > self.threshold or color[1] > self.threshold or color[2] > self.threshold

  def read(self, image):
    orange  = np.mean(np.asarray(image.crop((403, 249, 405, 251))), (0, 1), dtype=np.float32)
    red     = np.mean(np.asarray(image.crop((411, 249, 413, 251))), (0, 1), dtype=np.float32)
    pink    = np.mean(np.asarray(image.crop((427, 249, 429, 251))), (0, 1), dtype=np.float32)
    bit = (4 if self.isNotBlack(orange) else 0) + (2 if self.isNotBlack(red) else 0) + (1 if self.isNotBlack(pink) else 0)
    return NextReader.bitToPiece[bit]

class InGameChecker:
  normalRGB = None
  normalMask = None
  tetrisRGB = None
  tetrisMask = None
  def __init__(self):
    n = np.asarray(Image.open("assets/normal.png"), dtype=np.int16)
    InGameChecker.normal = n[:,:,0:3]
    InGameChecker.normalMask = n[:,:,3] / 255
    t = np.asarray(Image.open("assets/tetris.png"), dtype=np.int16)
    InGameChecker.tetris = t[:,:,0:3]
    InGameChecker.tetrisMask = t[:,:,3] / 255
    self.threshold = 15000

  def setThreshold(self, threshold):
    self.threshold = threshold

  def check(self, smallImage):
    array = np.asarray(smallImage, dtype=np.int16)
    normalScore = np.sum(np.multiply(InGameChecker.normalMask, np.sum(np.abs(np.subtract(InGameChecker.normal, array)), axis=2)))
    tetrisScore = np.sum(np.multiply(InGameChecker.tetrisMask, np.sum(np.abs(np.subtract(InGameChecker.tetris, array)), axis=2)))
    minScore = min(normalScore, tetrisScore)
    return minScore < self.threshold

class DigitReader:
  digits = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f", "null"]
  digitImages = None
  digitArrays = None
  digitNumbers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 2, 13, 14, 15, -1]
  def __init__(self):
    if not DigitReader.digitImages:
      DigitReader.digitImages = [Image.open(f"assets/digit_{e}.png").convert("L") for e in DigitReader.digits]
      DigitReader.digitArrays = [np.asarray(e, dtype=np.int16) for e in DigitReader.digitImages]

  def read(self, image, hex, red):
    result = [(n, 255*14*14) for n in DigitReader.digitNumbers]
    mul = 3 if red else 1
    array = np.asarray(image.convert("L"), dtype=np.int16) * mul
    for i, comp in enumerate(DigitReader.digitArrays):
      if ((0 <= i and i <= 9) or i == 16) or hex:
        result[i] = (DigitReader.digitNumbers[i], np.sum(np.abs(np.subtract(comp, array))))
    return sorted(result, key=lambda x: x[1])

