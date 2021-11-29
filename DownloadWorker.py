from PyQt5.QtCore import QObject, pyqtSignal
from DownloadCtrl import DownloadCtrl
import time
class Worker(QObject):
  stop = pyqtSignal() # 终止下载
  finished = pyqtSignal() # 下载完成
  state = pyqtSignal(str, str) # 当前状态
  progress = pyqtSignal(int, int) # 总进度
  progress_ts = pyqtSignal(int) # ts分块下载进度

  def __init__(self, MainSelf):
    super().__init__()
    self.MainSelf = MainSelf
    self.downCtrl = DownloadCtrl(self, MainSelf)

  def run(self):
    for url in self.MainSelf.form['urls']:
        name = str(int(time.time()))
        if '|' in url:
          urls = url.split("|")
          url = urls[0]
          name = urls[1]
        if self.MainSelf.is_runing:
          self.downCtrl.startDownload(url, name)
    self.state.emit(self.MainSelf.lang['downState']['ready'], '')
    self.finished.emit()
