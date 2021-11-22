import requests
import re

class Url():
    def __init__(self, protocol=None, fullpath=None, name=None, query=None):
        self.protocol = protocol
        self.full_path = fullpath
        self.name = name
        self.query_str = query
        # TODO 更多url属性

class UrlParse:

    def is_access_url(self, url):
        resp = requests.get(url)
        if resp.status_code == 200:
            return True
        return False

    def urlsplit(self, url):
        # 手动添加?
        if '?' not in url:
            url += '?'
        pattern = re.compile(r'(http[s]:\/\/)(.*)\/(.*)\?(.*)')
        results = pattern.findall(url)
        if results:
            protocol, path, name, query = results[0]
            return Url(protocol, path, name, query)

    '''
      url: 一个可以访问的url
      slicePath: 分片路径，或者key路径
    '''

    def get_base_uri(self, url, slicePath):
        try:
            if self.is_url(url):
              m3u8_url_obj = self.urlsplit(url)
              if m3u8_url_obj:
                paths = m3u8_url_obj.full_path.split('/')
                if paths:
                    temp = f'{m3u8_url_obj.protocol}'
                    for index in paths:
                        temp += f'{index}/'
                        if self.is_access_url(f'{temp}{slicePath}'):
                            return f'{temp}'
        except Exception as err:
            print(f"get_m3u8_base_uri:{err}")
            raise err

    def is_url(self, url):
        if re.match(r'[\w\d]+:\/\/', url):
            return True
        return False