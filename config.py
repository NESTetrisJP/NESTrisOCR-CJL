import json

class Config:
  def __init__(self):
    self.preview = True
    self.enableSettings = False
    self.captureWindowName = "ウィンドウ プロジェクタ"
    self.showGrid = False
    self.showStencil = False
    self.xCoord = 0
    self.yCoord = 0
    self.width = 400
    self.height = 400
    self.enableSettingsExpert = False
    self.captureFPS = 60
    self.sendFPS = 5
    self.windowHandle = 0
    self.blackThreshold = 25
    self.inGameThreshold = 30000

  def load(self):
    try:
      with open("config.json", mode="r") as f:
        hash = json.loads(f.read())
        def isValid(key, typ):
          return key in hash and type(hash[key]) == typ
        if isValid("preview", bool): self.preview = hash["preview"]
        if isValid("enableSettings", bool): self.enableSettings = hash["enableSettings"]
        if isValid("captureWindowName", str): self.captureWindowName = hash["captureWindowName"]
        if isValid("showGrid", bool): self.showGrid = hash["showGrid"]
        if isValid("showStencil", bool): self.showStencil = hash["showStencil"]
        if isValid("xCoord", int): self.xCoord = hash["xCoord"]
        if isValid("yCoord", int): self.yCoord = hash["yCoord"]
        if isValid("width", int): self.width = hash["width"]
        if isValid("height", int): self.height = hash["height"]
        if isValid("enableSettingsExpert", bool): self.enableSettingsExpert = hash["enableSettingsExpert"]
        if isValid("captureFPS", int): self.captureFPS = hash["captureFPS"]
        if isValid("sendFPS", int): self.sendFPS = hash["sendFPS"]
        if isValid("windowHandle", int): self.windowHandle = hash["windowHandle"]
        if isValid("blackThreshold", int): self.blackThreshold = hash["blackThreshold"]
        if isValid("inGameThreshold", int): self.inGameThreshold = hash["inGameThreshold"]
    except:
      pass

  def save(self):
    try:
      with open("config.json", mode="w") as f:
        f.write(json.dumps({
          "preview": self.preview,
          "enableSettings": self.enableSettings,
          "captureWindowName": self.captureWindowName,
          "showGrid": self.showGrid,
          "showStencil": self.showStencil,
          "xCoord": self.xCoord,
          "yCoord": self.yCoord,
          "width": self.width,
          "height": self.height,
          "enableSettingsExpert": self.enableSettingsExpert,
          "captureFPS": self.captureFPS,
          "sendFPS": self.sendFPS,
          "windowHandle": self.windowHandle,
          "blackThreshold": self.blackThreshold,
          "inGameThreshold": self.inGameThreshold
        }))
    except:
      pass