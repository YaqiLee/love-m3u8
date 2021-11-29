from contextlib import closing
import subprocess
from Crypto.Cipher import AES
from multiprocessing.pool import ThreadPool
import requests
import os
from ffmpy3 import FFmpeg
import m3u8
import shutil
from DownUrlParse import UrlParse

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"}

ajax = requests.session()
adapter = requests.adapters.HTTPAdapter(max_retries=5)
ajax.mount('http', adapter)

urlparse = UrlParse()

class DownloadCtrl:
    def __init__(self, worker, main):
        self.worker = worker
        self.main = main
        self.form = main.form
        self.lang = main.lang

    def startDownload(self, url, fileName):
        
        try:
            # 1. 是否正确的url地址
            if urlparse.is_url(url) == False:
                return
            # 2. 是否正常获取m3u8内容
            self.base_url = url
            self.url_base_path = None
            self.m3u8_obj = self.get_m3u8_body(url)
            self.m3u8_obj_size = len(self.segments_uri)
            # 生成文件名
            self.temp_file_name = fileName
            # key解密
            self.cipher_box = self.get_cipher_box()
            # 输出目录
            self.save_path = self.formatPath(self.form['save_path'])
            # 临时文件目录
            self.file_dir = self.formatPath(f'{os.getcwd()}/output/{self.temp_file_name}')
            # urls路径，用于ffmpeg合并分片文件
            self.url_file_path = "{}/urls.txt".format(self.file_dir)
            self.worker.state.emit(self.downState['downloading'], self.temp_file_name)
            
            if os.path.exists(self.file_dir) == False:
                os.makedirs(self.file_dir)

            if os.path.exists(self.url_file_path):
              print("\n删除urls.txt")
              os.remove(self.url_file_path)

            for index in range(self.m3u8_obj_size):
                if self.main.is_runing == False:
                  return
                ts_file_name = "{}_{}.ts".format(self.temp_file_name, f'{index}'.zfill(4))
                ts_file_path = "{}/{}".format(self.file_dir, ts_file_name)
                ts_url = self.get_valid_url(url, self.segments_uri[index])
                  
                self.worker.progress.emit(index + 1, self.m3u8_obj_size)

                with ThreadPool() as pool:
                    # 同步方式
                  if os.path.exists(ts_file_path) == False:
                    pool.apply(self.down_file, args={(ts_url, ts_file_path), })
                  self.save_url(ts_file_name)
            # 设置完成状态
            self.send_state(self.downState['finish'])
            self.merge_ts(self.main.fileName)
            self.send_state(self.downState['clear'])
            # 清理临时文件
            shutil.rmtree(self.file_dir)
            print("\n清理完成！")

        except Exception as err:
            print(err)
    def send_state(self, state, fileName = None):
      self.worker.state.emit(state, fileName)

    def get_valid_url(self, url, tsPath):
        try:
            if urlparse.is_url(tsPath) == False:
                if self.url_base_path == None:
                    self.url_base_path = urlparse.get_base_uri(url, tsPath)
                    print('url_base_path:' + self.url_base_path)
                return f"{self.url_base_path}{tsPath}"
            return tsPath
        except Exception as err:
            print("get_valid_url：获取ts地址失败")
            raise err
    def save_url(self, url):
        try:
            # r:read w:write a:append
            with open(self.url_file_path, 'a') as f:
                path = os.path.join(os.getcwd(), os.path.normpath(self.file_dir), url)
                f.write("file \'{}\' \n".format(path))
        except Exception as err:
            print("save_url:保存url失败\n")
            raise err

    def get_cipher_box(self):
        try:
            print('---get_cipher_box---')
            # TODO 自定义keybaseurl
            key_obj = self.get_key_obj()
            if key_obj:
                key_url = self.get_valid_url(self.base_url, key_obj.uri)
                print(f'key_url: {key_url}')
                resp = ajax.get(key_url)
                # TODO 自定义解密方式
                return AES.new(resp.content, AES.MODE_CBC)
        except Exception as err:
            print("get_cipher_box:解析key失败")
            raise err

    def get_key_obj(self):
        for key in self.m3u8_obj.keys:
            if key:  # First one could be None
                print(key.uri)
                print(key.method)
                print(key.iv)
                return key

    def down_file(self, params):
        try:
            url, filePath = params
            with closing(ajax.get(url, headers=headers, stream=True, timeout=60)) as response:
                chunk_size = 1024  # 单次请求最大值
                content_size = int(
                    response.headers['content-length'])  # 内容体总大小
                data_count = 0
                with open(filePath, 'wb+') as f:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            if self.cipher_box:
                                f.write(self.cipher_box.decrypt(chunk))
                            else:
                                f.write(chunk)

                            data_count = data_count + len(chunk)
                            down_rate = (data_count / content_size) * 100
                            self.worker.progress_ts.emit(down_rate)
                            print("\r 文件下载进度：%d%%(%d/%d) - %s" % (down_rate,
                                  data_count, content_size, filePath), end=" ")
        except Exception as err:
            os.remove(filePath)
            print("下载失败: {}\n\r{}".format(url, err))

    # 解析m3u8
    def get_m3u8_body(self, url):
        print('---get_m3u8_body---')
        try:
          resp = m3u8.load(url)
          if resp.data['playlists']:
              play_uri = resp.data['playlists'][0]['uri']
              valid_url = self.get_valid_url(url, play_uri)
              print(f'解析url {valid_url}')
              return m3u8.load(f"{valid_url}")
          else:
              return resp
        except Exception as err:
          print("解析url失败！")
          raise err

    def merge_ts(self, name):
        try:
            self.merge_ts_by_shell(name)
        except:
            self.merge_ts_by_ffmpeg(name)

    # ffmpeg合并ts
    def merge_ts_by_ffmpeg(self, name):
        try:
            # 转换文件格式
            merge_format = self.form['output_format']
            output_name = f'{name}.{merge_format}'
            output_path = os.path.join(self.save_path, output_name)
            FFmpeg(executable="ffmpeg.exe", inputs={"{}/urls.txt".format(self.file_dir): '-err_detect ignore_err -f concat -safe 0 -threads 4 -noautorotate'},
                        outputs={'{}'.format(output_path): '-hide_banner -y -c copy'}).run()
            print('合并完成！')
        except Exception as err:
            print("合并失败！");
            raise err
    # cmd合并
    def merge_ts_by_shell(self, name):
        try:
            # 转换文件格式
            merge_format = self.form['output_format']
            output_name = f'{name}.{merge_format}'
            tsPath = os.path.join(self.file_dir, '*.ts')
            output_path = os.path.join(self.save_path, output_name)
            proc = subprocess.Popen(['copy', '/b', tsPath, output_path], shell=True)
            proc.communicate()
        except Exception as err:
            print("合并出错")
            raise err

    def gen_file_dir(self, path):
        if os.path.isdir(path) == False:
            os.makedirs(path)

    def is_url(self, uri):
        return uri.startswith(('https://', 'http://'))

    @property
    def segments_uri(self):
        try:
            return self.m3u8_obj.segments.uri
        except:
            print("没有分片")

    @property
    def downState(self):
        return self.lang['downState']
    
    def formatPath(self, path):
        return path.replace(r'\/'.replace(os.sep, ''), os.sep)
