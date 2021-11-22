class I3u8:
  language = {
    "zh_CN":{
      "downState": {
        "ready": "准备下载",
        "downloading": "正在下载",
        "finish":"下载完成，正在合并",
        "clear": "合并完成，清理临时文件"
      }
    },
    "en_US":{
      "downState": {
        "ready": 'Ready To Download',
        "finish":"Video merging"
      }
    }
  }

  def __init__(self, locate):
    self.locate = locate
  
  @property
  def lang(self):
    for label in self.language:
      if label == self.locate:
        return self.language[label]
    return self.language['zh_CN']
