from PyQt5.QtCore import QObject, QThread, pyqtSignal, QTimer, QMutex, QIODevice, pyqtSlot
from PyQt5.QtNetwork import QTcpSocket
import json
import time
import numpy as np # TODO

class NetworkWorker(QObject):
  finished = pyqtSignal()

  def __init__(self):
    super().__init__()
    self.timer = None
    self.socket = None
    self.data = []

  def start(self):
    self.timer = QTimer(self)
    self.socket = QTcpSocket(self)
    self.socket.connectToHost("127.0.0.1", 5041, QIODevice.ReadWrite)
    if self.socket.waitForConnected(5000):
      self.socket.write(json.dumps({ "userName": "test", "key": "key" }).encode("utf-8"))
    self.timer.timeout.connect(self.update)
    self.timer.start(200)

  @pyqtSlot()
  def end(self):
    self.socket.disconnectFromHost()
    if self.socket.state() != QTcpSocket.UnconnectedState:
      self.socket.waitForDisconnected(5000)
    self.timer.stop()
    self.finished.emit()
    self.thread().quit()

  def update(self):
    self.socket.write(json.dumps({
      "timeSent": time.time_ns() // 1000000,
      "data": self.data
    }).encode("utf-8"))
    self.data = []

  def accumulate(self, result):
    if result["success"] and result["inGame"]:
      field = np.ndarray.flatten(result["field"]).tolist()
      self.data.append({
        "time": time.time_ns() // 1000000,
        "field": field,
        "score": result["score"],
        "level": result["level"],
        "next": result["next"],
        "lines": result["lines"]
        # "stats":
      })