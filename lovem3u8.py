from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread
import sys
import DownloadUi
from DownloadWorker import Worker
from I3u8Config import I3u8

class Downloader(QtWidgets.QMainWindow, DownloadUi.Ui_Form):
  def __init__(self, parent=None):
    super(Downloader, self).__init__(parent)
    self.lang = I3u8('zb_CN').lang
    self.setupUi(self)

  def onStartClick(self):
    self.is_runing = True
    if self.formData() == None:
      return
    self.startDownload()
    self.stopDownloadBtn.setEnabled(True)
  
  def onStopClick(self):
    self.is_runing = False
    self.downThread.quit()
    self.downThread.wait()
    self.startDownloadBtn.setEnabled(True)
    self.stopDownloadBtn.setEnabled(False)
  
  def finishDownload(self):
    self.startDownloadBtn.setEnabled(True)
    self.stopDownloadBtn.setEnabled(False)
    self.fileNameLabel.setText('')

  def reportState(self, text, fileName = None):
    self.stateLabel.setText(text)
    if fileName:
      self.fileNameLabel.setText(fileName)

  # 总下载进度
  def reportProgress(self, index, size):
    self.progressLabel.setText("{}/{}".format(index, size))

  # ts现在进度
  def reportTsProgress(self, size):
    self.progressBar.setProperty('value', size)

  def reportStop():
    pass

  def startDownload(self):
    self.downThread = QThread()
    self.worker = Worker(self)
    self.worker.moveToThread(self.downThread)
    self.downThread.started.connect(self.worker.run)
    self.worker.finished.connect(self.downThread.quit)
    self.worker.finished.connect(self.worker.deleteLater)
    self.worker.progress.connect(self.reportProgress)
    self.worker.state.connect(self.reportState)
    self.worker.progress_ts.connect(self.reportTsProgress)
    self.worker.stop.connect(self.reportStop)
    self.downThread.start()

    self.startDownloadBtn.setEnabled(False)
    self.downThread.finished.connect(self.finishDownload)


def main():
  app = QApplication(sys.argv)
  form = Downloader()
  form.show()
  form.center()
  sys.exit(app.exec_())

if __name__ == '__main__':
  main()