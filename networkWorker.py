from PyQt5.QtCore import QObject, QThread, pyqtSignal, QTimer, QMutex, QIODevice, pyqtSlot
from PyQt5.QtNetwork import QTcpSocket
import json
import time
import numpy as np # TODO

PACKET_VERSION = 0

class NetworkWorker(QObject):
  updateStatus = pyqtSignal(str)
  finished = pyqtSignal()

  def __init__(self, config):
    super().__init__()
    self.config = config
    self.timer = None
    self.socket = None
    self.socketAliveTimer = None
    self.data = []

  def start(self):
    self.timer = QTimer(self)
    self.timer.timeout.connect(self.update)
    self.timer.start(1000 / self.config.sendFPS)
    self.socketAliveTimer = QTimer(self)
    self.socketAliveTimer.timeout.connect(self.updateSocketAlive)
    self.socketAliveTimer.start(3000)
    self.establishSocket()

  def establishSocket(self):
    self.socket = QTcpSocket(self)
    self.socket.disconnected.connect(self.onDisconnected)
    self.socket.error.connect(self.onError)
    self.updateStatus.emit("接続中")
    [host, _, port] = self.config.address.partition(":")
    self.socket.connectToHost(host, int(port), QIODevice.ReadWrite)
    if self.socket.waitForConnected(5000):
      self.updateStatus.emit("ログイン中")
      self.socket.write(json.dumps({ "userName": self.config.playerName, "key": self.config.accessKey, "version": PACKET_VERSION }).encode("utf-8"))
      self.updateStatus.emit("接続")
    else:
      self.updateStatus.emit("接続失敗")
      self.socket = None

  def onDisconnected(self):
    self.socket = None
    self.updateStatus.emit("切断されました")

  def onError(self):
    self.socket.abort()
    self.socket = None
    self.updateStatus.emit("接続エラー")

  def updateSocketAlive(self):
    if not self.socket:
      self.establishSocket()

  @pyqtSlot()
  def end(self):
    if self.socket:
      self.socket.disconnectFromHost()
      if self.socket and self.socket.state() != QTcpSocket.UnconnectedState:
        self.socket.waitForDisconnected(5000)
    self.timer.stop()
    self.finished.emit()
    self.thread().quit()

  def update(self):
    if self.socket:
      self.socket.write(json.dumps({
        "timeSent": time.time_ns() // 1000000,
        "data": self.data
      }).encode("utf-8"))
    self.data = []

  def accumulate(self, result):
    if result["success"] and result["inGame"]:
      field = np.ndarray.flatten(result["field"]).tolist()
      self.data.append({
        "time": result["time"],
        "field": field,
        "score": result["score"],
        "level": result["level"],
        "next": result["next"],
        "lines": result["lines"]
        # "stats":
      })