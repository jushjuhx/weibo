__author__ = 'hope'
#封装一些http操作
import urllib.request , configparser , chardet , http_gzip
#获取config配置文件def getConfig(section, key). 设置user-agent信息
config = configparser.ConfigParser()
config.read('config.ini')
user_agent = config.get('user_agent', 'ua_uc')

# 封装一个用于get 的函数
def getData(url,headers = {'User-Agent' : user_agent,'Accept-Encoding':'gzip'}) :
    request = urllib.request.Request(url,headers=headers)
    response = urllib.request.urlopen(request)
    text = response.read()
    if(response.info()['Content-Encoding'] == 'gzip'):
        text = http_gzip.gzipdecode(text)
    body = text.decode(chardet.detect(text)['encoding'],'ignore')
    return body

# 封装一个用于post 的函数
def postData(url , data , headers = {'User-Agent' : user_agent,'Accept-Encoding':'gzip'}) :
    # 这里的urlencode用于把一个请求对象用'&'来接来字符串化，接着就是编码成utf-8
    data = urllib.parse.urlencode(data).encode('utf-8')
    request = urllib.request.Request(url , data , headers)
    response = urllib.request.urlopen(request)
    text = response.read()
    if(response.info()['Content-Encoding'] == 'gzip'):
        text = http_gzip.gzipdecode(text)
    body = text.decode(chardet.detect(text)['encoding'],'ignore')
    return body

